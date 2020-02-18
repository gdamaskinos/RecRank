# RecRank 
Author: Georgios Damaskinos (georgios.damaskinos@gmail.com)

_RecRank_ is a tool for exploiting black-box recommenders for algorithm selection, presented in [The Imitation Game: Algorithm Selection by Exploiting Black-Box Recommenders](http://netys.net/accepted-papers/).

## Main Components

### [recom.py](recom.py)
Executes recommendation algorithms from  and outputs the recommendations list

* Example execution:
	```bash
	python recom.py --topN_list 5 --dataset /fullPath/u.data --testSize 1000 --validSize 9000  --surprise_algo SVD --pickleSavePath /fullPath/list.pickle
	```

### [rec2graph.py](rec2graph.py)
Parses the output of a recommendation algorithm to a graph

* Example execution:
  ```bash
  python rec2graph.py --pickleLoadPath ./list.pickle --output ./graphs/graph.xml
  ```


### [distCalc.py](distCalc.py)
Calculates and visualizes the distance of recom algorithms

* Example execution:
  ```bash
  python distCalc.py --folder_paths  ./graphs/ --manual
  ``` 

## Usage

1. Create the dataset files by using the [splitter](parsers/splitter.py).
2. Create the commands file by using the [commandsCreator](deployment/commandsCreator.py).
3. Execute the commands in parallel by using the [runner](deployment/runner.sh).
4. Parse the results by using something similar to:
  ```bash
  export suf=kv.out && for file in *$suf; do echo -ne $(basename ${file%$suf}); awk -F: 'BEGIN {ORS=""}; /F1/ {print "\t",$2} END {print "\n"}' $file; done
  ```
5. Get the ideal ranking (known\_train + unknown\_test) by sorting the parsed output and put the ranked algorithm in a testRank.txt file.
6. Extract the graph for each output .pickle file (known\_train + known\_query, unknown\_train + known query for the black-box) by using the [rec2graph](rec2graph.py) method. Example: 
  ```bash
  for file in *kq.pickle; do name=${file%kq.pickle}; echo $name; python /path/to/rec2graph.py --pickleLoadPath $file --output ~/temp/$name.xml --topN 20 & done
  ```
7. Use the [distCalc](distCalc.py) to calculate the ranking correlation. Example:
  ```bash
  python distCalc.py --folder_paths ~/temp/ --manual --blackbox_path bb.xml --cmpRank_path testRank.txt
  ```

## License 
This project is licensed under the terms of BSD 3-clause Clear license.
by downloading this program, you commit to comply with the license as stated in the LICENSE.md file.
