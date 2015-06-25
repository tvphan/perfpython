Some quick tests, experiments and scripts for the CDS Perf Team

**Note**: at the moment all you need Python 2.6.x or Python 2.7.x, it is **not** Python 3.0 compatible yet

### Benchmarks, located in (./performanceTests)
Dependencies:
Note: if you have python 2.7.9 or newer, it includes pip, python's package manager
* python's requests library: http://docs.python-requests.org/en/latest/user/install/
  * with pip: pip install requests
* numpy library: http://sourceforge.net/projects/numpy/files/NumPy/
  * with pip: pip install numpy
* loremipsum library: https://pypi.python.org/pypi/loremipsum
  * with pip: pip install loremipsum

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
  * Getting started:
    1. clone this repo: `git clone git@github.ibm.com:malee/cdsperfplayground.git --recursive`
      * the above will clone the main repository and also pull the dependent submodule
    2. configure performanceTests/config.py to point to your cloudant instance
    3. cd into performanceTests
    4. run the test: python ./multThreadedBenchmarkDriver.py
      * Thread and run length can be set in ./multThreadedBenchmarkDriver.py
      * Action ratios can be set in benchmarkWorker.py
    5. get a coffee

### Misc related files:
1. **genPlots.py**
  * Generates some very simple plots
  * Calculated the number of errors during the run
2. **getTopStats.py**
  * gets the "CPU Steal Time" which is a measure of how many CPU cycles are lost due to CPU overcomitment 
