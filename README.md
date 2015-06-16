Some quick tests, experiments and scripts for the CDS Perf Team

### Benchmarks, located in (./performanceTests)
1. **basicCurdBenchmark.py**
  * This test creates a database and then does the following operations in order:
    * 500 inserts, simple docs
    * 500 bulk inserts, 10 simple docs per insert
    * 500 random reads
    * 500 random updates, one field updated each (also generates a read to get _rev)
    * 500 random deletes (also generates a read to get _rev)
2. **multThreadedBenchmarkDriver**
  * This test spawns a number (n_threads) of worker threads, each execute a number (runLength) of randomly selected operations
  * The operations are randomly selected to be in the following ratios:
    * 200 Inserts
    * 100 Deletes
    * 100 Updates
    * .. more to come
