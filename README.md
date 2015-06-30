Some quick tests, experiments and scripts for the CDS Perf Team

**Note**: at the moment all you need Python 2.6.x or Python 2.7.x, it is **not** Python 3.0 compatible yet

Dependencies:
Note: if you have python 2.7.9 or newer, it includes pip, python's package manager
* argparse, requests, numpy, matplotlib
* if you want to use a virtualenv:
  * `virtualenv testenv`
  * `source ./testenv/bin/activate`
* Install requirements using pip:
  * `pip install -r requirements.txt`

### Getting started:
  1. clone this repo: `git clone git@github.ibm.com:malee/cdsperfplayground.git --recursive`
    * the above will clone the main repository and also pull the dependent submodule
  2. configure performanceTests/config.py to point to your cloudant instance
  3. cd into performanceTests
  4. run the test: `python ./multThreadedBenchmarkDriver.py`
    * Thread count, run length and action-ratios can be set in config.py
  5. get a coffee

### Benchmarks, located in (./performanceTests)

1. **basicCrudBenchmark.py**
  * This test creates a database and then does the following operations in order:
    * 500 inserts, simple docs
    * 500 bulk inserts, 10 simple docs per insert
    * 500 random reads
    * 500 random updates, one field updated each (also generates a read to get _rev)
    * 500 random deletes (also generates a read to get _rev)
2. **multThreadedBenchmarkDriver.py**
  * This test spawns a number (n_threads) of worker threads, each execute a number (runLength) of randomly selected operations
  * The operations are randomly selected to be in the following ratios:
    * 50 Inserts
    * 25 Deletes
    * 25 Updates
    * 25 Reads
    * 5 Bulk Inserts
  * Currently this test can run 1000 users concurrently on a single laptop
3. **multThreadedBenchmarkDriver_ironClone.py**
  * This is an exact clone of IronCushion
  * This test spawns 100 worker threads, each execute 20 bulk inserts of 1000 documents modeled after performanceTests/templates/iron_template.json
  * Then each worker thread executes 1000 randomly selected actions according to the following ratios:
    * 2 Inserts
    * 3 Deletes
    * 3 Updates
    * 2 Reads
  * Note: config.py is only used for the database credentials and database name for this project, the rest is preset to mimic ironcushion

### Misc related files:
1. **genPlots.py**
  * Generates some very simple plots
  * Calculated the number of errors during the run
2. **getTopStats.py**
  * gets the "CPU Steal Time" which is a measure of how many CPU cycles are lost due to CPU overcomitment 
