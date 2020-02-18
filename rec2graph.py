"""
  Copyright (c) 2019 - Present – Thomson Licensing, SAS
  All rights reserved.
  @author Georgios Damaskinos <georgios.damaskinos@gmail.com>

  This source code is licensed under the Clear BSD license found in the
  LICENSE file in the root directory of this source tree.
 """



"""Transforms the output of the recommendation algorithm into a graph"""

from graph_tool.all import *
from surprise import SVD, KNNBasic
import numpy as np
import random
import sys
import argparse
import os
import pickle

def gexfFormat(profile, recom, filename):
  """Outputs the recommendation graph in gexf format

  Parameters:
    profile (list): user profile as [(iid1, r1, ts1), ...] sorted by timestamp
    recom (list): topN recom for every click
      [[(iid11, pred11), ... (iid1N, pred1N)],
       [(iid21, pred21), ... (iid2N, pred2N)],
       ...]
  """
  # ! ids are raw -> strings
  clickedItems = set(map(lambda x: str(x[0]), profile)) # set of clicked items
  recomItems = set() # set of recommended items

  with open(filename, 'w') as f:
    # write header
    f.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
    f.write("""<gexf xmlns:viz="http:///www.gexf.net/1.2/viz" version="1.2" xmlns="http://www.gexf.net/1.2">\n""")
    f.write("""<graph defaultedgetype="undirected" idtype="string" type="static">\n""")

    # write edges
    f.write("""<edges>\n""")
    id = 0
    for click in range(0, len(profile)): # for all the clicks
      print("Number of processed clicks: ", click)
      for rec in recom[click]: # for the topN recommendations
        f.write("<edge id=\"" + str(id) + "\" source=\"" + str(rec[0]) + "\" target=\"" + str(profile[click][0]) + "\" weight=\"" + str(rec[1]) + "\"/>\n")
        recomItems.add(str(rec[0]))
        id += 1

    f.write("""</edges>\n""")

    f.write("""<nodes>\n""")
    # write clicked item-nodes in an outter ring
    angleStep = 2*np.pi / float(len(clickedItems)) # polar coordinates angle step
    angle = 0 # polar coordinates angle [0, 2pi]
    R = 1000 # outter
    for item in clickedItems: # for all the clicks
      target = str(item)
      f.write("<node id=\"" + target + "\">\n")
      f.write("\t")
      f.write("""<viz:color r="255" g="0" b="0"></viz:color>\n""") # red color
      f.write("<viz:position x=\"" + str(R * np.cos(angle)) + "\" y=\"" + str(R * np.sin(angle)) + "\" z=\"0.0\"/>") # ring position
      f.write("</node>\n")
      angle += angleStep

    # write the rest item-nodes in an inner ring
    angleStep = 2*np.pi / float(len(recomItems - clickedItems)) # polar coordinates angle step
    angle = 0 # polar coordinates angle [0, 2pi]
    R = 600 # outter
    for item in recomItems - clickedItems: # for the rest of the items
      target = str(item)
      f.write("<node id=\"" + target + "\">\n")
      f.write("\t")
      f.write("<viz:position x=\"" + str(R * np.cos(angle)) + "\" y=\"" + str(R * np.sin(angle)) + "\" z=\"0.0\"/>") # ring position
      f.write("</node>\n")
      angle += angleStep

    f.write("""</nodes>\n""")
    f.write("""</graph>\n</gexf>""")

def graph_tool2hop(profile, recom, filename):
  """Outputs the recommendation graph as a graph-tool Graph() object
  Graph has two rings (2hop)
  Vertices (red): outer ring contains the clicked items
  Vertices (blue): inner ring contains the recommended \setminus clicked items
  Edge between item A, B <=> B was recommended to the user after click A
  edge weight = rating prediction

  Args:
    profile (list): user profile as [(iid1, r1, ts1), ...] sorted by timestamp
    recom (list): topN recom for every click
      [[(iid11, pred11), ... (iid1N, pred1N)],
       [(iid21, pred21), ... (iid2N, pred2N)],
       ...]
    filename (string): path with extension specifing the output type (e.g. out.xml)

  Returns:
    graph_tool.Graph: recommendation graph
  """
  g = Graph()

  # ! ids are raw -> strings
  clickedItems = set(map(lambda x: str(x[0]), profile)) # set of clicked items
  recomItems = set() # set of recommended items

  # get recommended items
  for click in range(0, len(profile)): # for all the clicks
    for rec in recom[click]: # for the topN recommendations
      recomItems.add(str(rec[0]))

  # construct vertices
  vert = {} # dictionary: iid -> Vertex object
  color_prop = g.new_vertex_property('vector<double>') # vertex color dict
  pos_prop = g.new_vertex_property('vector<double>') # vertex coordinates dict
  text_prop = g.new_vertex_property("string") # vertex text

  # write clicked item-nodes in an outter ring
  angleStep = 2*np.pi / float(len(clickedItems)) # polar coordinates angle step
  angle = 0 # polar coordinates angle [0, 2pi]
  R = 1000 # outter
  for item in clickedItems: # for all the clicks
    target = str(item)
    vert[target] = g.add_vertex()
    color_prop[vert[target]] = [255,0,0,1] # RGBA format
    pos_prop[vert[target]] = [R * np.cos(angle), R * np.sin(angle)]
    text_prop[vert[target]] = target

    angle += angleStep

  # write the rest item-nodes in an inner ring
  angleStep = 2*np.pi / float(len(recomItems - clickedItems)) # polar coordinates angle step
  angle = 0 # polar coordinates angle [0, 2pi]
  R = 600 # outter
  for item in recomItems - clickedItems: # for the rest of the items
    target = str(item)
    vert[target] = g.add_vertex()
    color_prop[vert[target]] = [0,0,255,1] # RGBA format
    pos_prop[vert[target]] = [R * np.cos(angle), R * np.sin(angle)]
    text_prop[vert[target]] = target

    angle += angleStep

  # construct edges
  edges = {} # dictionary: (source_iid, target_iid) -> Vertex object
  weight_prop = g.new_edge_property('float')

  for click in range(0, len(profile)): # for all the clicks
    for rec in recom[click]: # for the topN recommendations
      target= str(rec[0])
      source = str(profile[click][0])
      weight = rec[1]

      edges[(source, target)] = g.add_edge(vert[source], vert[target])
      weight_prop[edges[(source, target)]] = weight

  # save properties to graph
  g.vertex_properties["color"] = color_prop
  g.vertex_properties["pos"] = pos_prop
  g.vertex_properties["text"] = text_prop
  g.edge_properties["weight"] = weight_prop

  # save graph
  g.save(filename)

  return g

def itemGraphUpdate(clicked_iid, recom, graph=None, weight=True):
  """Updates the recommendation graph as a graph-tool Graph() object
  Vertices: recommended and/or clicked items
  Edge A, B <=> itemB is at least in one user recom list triggered by click A
  EdgeAB scoreSum = \sum_{users} prediction for B after clicked A
  EdgeAB scoreCount = # predictions for B after clicked A
  if not weight:
    The scores for each recommendation are ignored.
    Multiple recommendations -> multiple edges between the same nodes

  Args:
    g (graph_tool.Graph): previous recommendation graph.
      if None then a new graph is constructed.
    clicked_uid (str)
    clicked_iid (str)
    recom (list): topN recom that the clicked item triggered
       [(iid1, pred1), ... (iidN, predN)]
    weight (boolean)

  Returns:
    graph_tool.Graph: updated recommendation graph

  """
  if graph is None:
    g = Graph()
    vert = {} # dictionary: iid -> Vertex object
    text_prop = g.new_vertex_property("string") # vertex text
    scoreSum_prop = g.new_edge_property('float')
    scoreCount_prop = g.new_edge_property('int')
  else:
    g = graph
    text_prop = g.vertex_properties["text"]
    scoreSum_prop = g.edge_properties["scoreSum"]
    scoreCount_prop = g.edge_properties["scoreCount"]


  # ! ids are raw -> strings
  clicked_iid = str(clicked_iid)

  # add vertices
  rec_ids = set(map(lambda x: str(x[0]), recom))
  for iid in rec_ids.union(set([clicked_iid])):
    # append if vertex does not exist
    if graph is None or find_vertex(g, g.vertex_properties["text"], iid) == []:
      v = g.add_vertex()
      text_prop[v] = iid

  # save properties to graph
  g.vertex_properties["text"] = text_prop

  # add edges
  src = find_vertex(g, g.vertex_properties["text"], clicked_iid)
  for iid, pred in recom:
    dst = find_vertex(g, g.vertex_properties["text"], iid)
    if weight:
      e = g.edge(src[0], dst[0], add_missing=True)
    else:
      e = g.add_edge(src[0], dst[0], add_missing=True)
#    print("Old scoreSum for edge (%s -> %s): %.2f" % (clicked_iid, iid, scoreSum_prop[e]))
    scoreSum_prop[e] += pred
    scoreCount_prop[e] += 1

  # save properties to graph
  g.edge_properties["scoreSum"] = scoreSum_prop
  g.edge_properties["scoreCount"] = scoreCount_prop

  return g

def userItemGraphUpdate(clicked_uid, clicked_iid, recom, graph=None, weight=True):
  """Updates the recommendation graph as a graph-tool Graph() object
  Vertices: recommended items and users
  Edge A, B <=> item A \in topn for user B
  EdgeAB scoreSum = score sum for item B from user A
  EdgeAB scoreCount = number of times item B was recommended to user A
  if not weight:
    The scores for each recommendation are ignored.
    Multiple recommendations -> multiple edges between the same nodes

  Args:
    g (graph_tool.Graph): previous recommendation graph.
      if None then a new graph is constructed.
    clicked_uid (str)
    clicked_iid (str)
    recom (list): topN recom that the clicked item triggered
       [(iid1, pred1), ... (iidN, predN)]
    weight (boolean)

  Returns:
    graph_tool.Graph: updated recommendation graph

  """
  if graph is None:
    g = Graph()
    vert = {} # dictionary: iid, uid -> Vertex object
    text_prop = g.new_vertex_property("string") # vertex text
    scoreSum_prop = g.new_edge_property('float')
    scoreCount_prop = g.new_edge_property('int')
  else:
    g = graph
    text_prop = g.vertex_properties["text"]
    scoreSum_prop = g.edge_properties["scoreSum"]
    scoreCount_prop = g.edge_properties["scoreCount"]


  # ! ids are raw -> strings
  clicked_iid = str(clicked_iid)
  clicked_uid = str(clicked_uid)

  # add item vertices
  rec_ids = set(map(lambda x: str(x[0]), recom))
  for iid in rec_ids:
    # append if vertex does not exist
    if graph is None or find_vertex(g, g.vertex_properties["text"], 'i_' + iid) == []:
      v = g.add_vertex()
      text_prop[v] = 'i_' + iid

  # add user vertice
  if graph is None or find_vertex(g, g.vertex_properties["text"], 'u_' + clicked_uid) == []:
    v = g.add_vertex()
    text_prop[v] = 'u_' + clicked_uid

  # save properties to graph
  g.vertex_properties["text"] = text_prop

  # add edges
  src = find_vertex(g, g.vertex_properties["text"], 'u_' + clicked_uid)
  for iid, pred in recom:
    dst = find_vertex(g, g.vertex_properties["text"], 'i_' + iid)
    if weight:
      e = g.edge(src[0], dst[0], add_missing=True)
    else:
      e = g.add_edge(src[0], dst[0], add_missing=True)
#    print("Old scoreSum for edge (%s -> %s): %.2f" % (clicked_uid, iid, scoreSum_prop[e]))
#    print(g.num_edges())
    scoreSum_prop[e] += pred
    scoreCount_prop[e] += 1

  # save properties to graph
  g.edge_properties["scoreSum"] = scoreSum_prop
  g.edge_properties["scoreCount"] = scoreCount_prop

  return g


def normalizedWeight(g, weight=True):
#  """EdgeAB weight = scoreSum - (\sum_{scoreSum} / \sum_{scoreCount}) + 1
  """
  if weight:
    EdgeAB weight = scoreSum / (\sum_{scoreSum} / \sum_{scoreCount})
    i.e., show the deviation of each prediction from the mean to make the
    weights from different graphs comparable
  else:
    EdgeAB weight = 1
  """
  weight_prop = g.new_edge_property('float')

  scoreSum_prop = g.edge_properties["scoreSum"]
  scoreCount_prop = g.edge_properties["scoreCount"]

  s = 0
  for scoreSum in scoreSum_prop:
    s += scoreSum

  c = 0 # will be = # test examples X N
  for scoreCount in scoreCount_prop:
    c += scoreCount

  avgPred = s / float(c)
  print("Average score: ", avgPred)

  weights = []
  for e in g.edges():
    if weight:
      tmp = scoreSum_prop[e] / avgPred * 100
      weights.append(tmp)
      weight_prop[e] = tmp
    else:
      tmp = 1
      weights.append(tmp)
      weight_prop[e] = tmp

  print("Number of edges: %s" % len(weights))
  print("Weights avg: %.4f and std: %.4f" % (np.mean(weights), np.std(weights)))

  g.edge_properties["weight"] = weight_prop

  return g

def graph_toolFull(recom, filename, thres=5):
  """Outputs the full recommendation graph as a graph-tool Graph() object
  See itemGraphUpdate() or userItemGraphUpdate for properties description

  Args:
    recom (list): topN recom for every click
      [(uid1, iid1, ts1, [(iid11, pred11), ... (iid1N, pred1N)]),
       ...]
    filename (string): path with extension specifing the output type (e.g. out.xml)
    thres (int): threshold for topN recommendations

  Returns:
    graph_tool.Graph: full recommendation graph
  """
  g = None
  for uid, iid, ts, recomList in recom:
    g = itemGraphUpdate(iid, recomList[:thres], g, True)
#    g = userItemGraphUpdate(uid, iid, recomList, g, True)

  g = normalizedWeight(g, True)
  g.save(filename)


  return g

def main(args):

  parser = argparse.ArgumentParser(description='Recommender output TO graph')
  parser.add_argument("--output", action='store', default=True, \
      help='Output graph filename; extension defines the type (e.g., .xml)')
  parser.add_argument("--topN", type=int, default=5, action='store', \
      help= 'topN Threshold when creating recommendation graph; default=5')
  parser.add_argument("--pickleLoadPath", type=str, default=True, \
      action='store', help='Pickle file to load topN recoms list')

  args = parser.parse_args()

  random.seed(42) # reproducability
  np.random.seed(42)

  with open(args.pickleLoadPath, 'rb') as handle:
    recs = pickle.load(handle)

  graph_toolFull(recs, args.output)

if __name__ == "__main__":
  main(sys.argv[1:])


