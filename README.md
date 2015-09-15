Some quick tests, experiments and scripts for the CDS Perf Team

**Note**: at the moment all you need Python 2.6.x or Python 2.7.x, it is **not** Python 3.0 compatible yet

Dependencies:
Note: if you have python 2.7.9 or newer, it includes pip, python's package manager, if you are on windows grab 32bit python
* argparse, requests, numpy, matplotlib
* if you want to use a virtualenv:
  * `virtualenv testenv`
  * `source ./testenv/bin/activate`
* Windows may additionally require these python packages
  * sudo apt-get -y install python-dev
  * sudo apt-get -y install python-lxml 
* Install requirements using pip:
  * `pip install -r requirements.txt`
* **If you are on Windows, you'll need to manually install numpy separately**
  * grab the newest **32bit** installer for your version of python here: http://sourceforge.net/projects/numpy/files/NumPy/1.9.2/
  * then you'll want to run: `python -m pip install win_requirements.txt`
  * and might also need: `pip install pyopenssl ndg-httpsclient pyasn1`
### Getting started:
  1. clone this repo: `git clone git@github.ibm.com:CloudDataServices/perf-cloudant-benchmark.git --recursive`
    * the above will clone the main repository and also pull the dependent submodules
  2. configure performanceTests/config.py to point to your cloudant instance
  3. cd into performanceTests
  4. if you created a virtualenv:
    * enter the virtualenv: `source ./testenv/bin/activate`
    * make sure you point to the testenv you created earlier
  5. run the test: `python ./cloudantBenchmark.py`
    * Thread count, run length and action-ratios can be set in config.py
  6. get a coffee

### Benchmarks, located in (./performanceTests)

1. **basicCrudBenchmark.py [deprecated]**
  * This test creates a database and then does the following operations in order:
    * 500 inserts, simple docs
    * 500 bulk inserts, 10 simple docs per insert
    * 500 random reads
    * 500 random updates, one field updated each (also generates a read to get _rev)
    * 500 random deletes (also generates a read to get _rev)
2. **cloudantBenchmark.py**
  * This test spawns a number (n_threads) of worker threads, each execute a number (runLength) of randomly selected operations
  * The operations are randomly selected to be in the following ratios(this can be changed in config.py):
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
1. **genPlots.py [deprected, use perf-analysis]**
  * Generates some very simple plots
  * Calculated the number of errors during the run
