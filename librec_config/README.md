# [librec](https://github.com/guoguibing/librec)

## Usage

* Execute with:
  ```bash
  git clone https://github.com/guoguibing/librec.git <clone_dir>
  sh <clone_dir>/bin/librec rec -exec -conf <prop.properties>
  ```
* [Examples on Real Data Sets](https://www.librec.net/release/v1.3/example.html)
* [Example algorithm properties](https://www.librec.net/dokuwiki/doku.php?id=AlgorithmList)
  ```properties
  rec.recommender.class=globalaverage
  dfs.data.dir=/
  dfs.result.dir=/path/to/result_dir
  # relative path for full dataset (i.e., file with concatenated trainSet and testSet)
  data.input.path=path/to/fullDataset.csv 
  # relative path for testset 
  data.testset.path=path/to/testSet.csv
  data.column.format=UIR
  data.model.splitter=testset
  rec.random.seed=42
  rec.eval.enable=true
  # false -> outputs the predictions for all the examples in the testSet 
  # true  -> outputs the topn recommendations for all the users in the dataSet
  rec.recommender.isranking=true
  rec.recommender.ranking.topn=5
  ```
