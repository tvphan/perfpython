'''
Created on Jun 13, 2015

@author: madmaze
'''
import unittest
import pyCloudantDB.pyCloudantDB as cdb
import config as c
import datetime as dt
import time
import json
import random
import logging
import traceback
import sys
from multiprocessing import Process, Queue, Value, Array
import benchmarkWorker as bW

class TestMultiThreadedDriver(unittest.TestCase):
    """ Basic Multithreaded benchmark """

    def setUp(self):
        self.randomIDs = None
        self.startTime = time.time()
        self.benchmarkConfig={
            "concurrentThreads" : 100,
            "bulkInsertsPerThread" : 20,
            "bulkInsertSize" : 1000,
            "iterationPerThread" : 1000,
            "actionRatios" : {
                  "simpleInsert" : 2,
                  "randomDelete" : 3,
                  "randomRead" : 2,
                  "randomUpdate" : 3,
                  "bulkInsert" : 0
                    }                   
            }
        """self.benchmarkConfig={
            "concurrentThreads" : 100,
            "iterationPerThread" : 1000,
            "bulkInsertsPerThread" : 20,
            "bulkInsertSize" : 1000,
            "actionRatios" : {
                  "simpleInsert" : 2,
                  "randomDelete" : 3,
                  "randomRead" : 2,
                  "randomUpdate" : 3,
                  "bulkInsert" : 0
                    }                   
            }"""

        self.threads = self.benchmarkConfig["concurrentThreads"]
        self.runLength = self.benchmarkConfig["iterationPerThread"]
        
        self.db = cdb.pyCloudantDB(c.config["dbConfig"])
        
        # test connection
        # TODO: capture the database version/build for output info
        respConn = self.db.testConnection()
        if not respConn.ok:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
        self.dbVersion = respConn.json()
        
        respDel = self.db.deleteDatabase(c.config["dbConfig"]["dbname"])
        
        # add database for test
        respAdd = self.db.addDatabase(c.config["dbConfig"]["dbname"])
        if not respAdd.ok:
            self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
            
    def tearDown(self):
        log = logging.getLogger('mtbenchmark')
        # dump test data
        log.info("test finished: " + str(dt.datetime.now()))
        log.info("Total "+self.testName+" run time:" + str(time.time()-self.startTime))
        json.dump(self.data, open("TaskData.json","w"))
        
        # Remove Database after test completion
        #respDel = self.db.deleteDatabase(c.config["dbConfig"]["dbname"])
        #if not respDel.ok:
        #    self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))

    def basicCrudWorker(self, insertedIDs, responseTimes, processStateDone, pid, activeThreadCounter, benchmarkConfig):
        ''' An instance of this is executed in every thread '''
        log = logging.getLogger('mtbenchmark')
        
        # increment out active thread count
        with activeThreadCounter.get_lock():
            activeThreadCounter.value += 1
            
        log.info("pid:%i started.." % pid)
        try:
            # Create a local DB object
            db = cdb.pyCloudantDB(c.config["dbConfig"])
            
            # Create a local Worker
            worker = bW.benchmarkWorker(db, insertedIDs, params=benchmarkConfig)
            
            
            for i in range(benchmarkConfig["iterationPerThread"]):
                try:
                    # TODO: add feature to allow exiting of all threads
                    #if any(processStateDone):
                    #    print pid, "error on other thread, exiting"
                    #    return False
                    
                    # Run worker 
                    resp = worker.execRandomAction(str(pid)+":"+str(i))
                    
                    if "err" in resp.keys() and resp["err"] is True:
                        log.error("("+str(pid)+") Task Level Error: " + resp["action"] + " - Exception: " + resp["msg"])
                    
                    # Stash response time
                    responseTimes.put(resp) #{"action":resp["action"], "resp":resp["delta_t"], "timestamp":resp["timestamp"]})
                
                except Exception as e:
                    # catch task level exception to prevent early exiting
                    e_info = sys.exc_info()[0]
                    errLine = "("+str(pid)+") Task Level Error - Exception: "+ str(e_info) + " trace:" + str(traceback.format_exc())
                    log.error(errLine)
                    
        except Exception as e:
            # catch thread level
            e_info = sys.exc_info()[0]
            errLine = "("+str(pid)+") Thread Level Exception - "+ str(e_info) + " trace:" + str(traceback.format_exc())
            log.error(errLine)
        
        processStateDone[pid]=True
        # decrement out active thread count
        with activeThreadCounter.get_lock():
            activeThreadCounter.value -= 1
        log.info("pid:%i finished.." % pid)
    
    def testMultiThreadedBenchmark(self):
        # setting up logging
        log = logging.getLogger('mtbenchmark')
        log.setLevel(logging.DEBUG)
        
        logStreamHandler = logging.StreamHandler()
        logStreamHandler.setLevel(logging.DEBUG)
        logStreamHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logFile = open("./run.log","w")
        logFileHandler = logging.StreamHandler(logFile)
        logFileHandler.setLevel(logging.DEBUG)
        logFileHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log.addHandler(logFileHandler)
        
        
        self.testName = "MultiThreadedBenchmark"
        self.data = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[],
                     "randomDelete":[],
                     "userCounts":[],
                     "dbVersion":self.dbVersion
                     }
        
        insertedIDs = Queue()
        responseTimes = Queue()
        #######################################################
        #
        # Bulk Inserts
        #
        #############
        activeThreadCounter = Value("i")
        processStateDone = Array('b',range(self.threads))
        for i in range(self.threads):
            processStateDone[i] = False
            
        bulkInsertConfig = {
            "concurrentThreads" : self.threads,
            "iterationPerThread" : self.benchmarkConfig["bulkInsertsPerThread"],
            "bulkInsertSize" : self.benchmarkConfig["bulkInsertSize"],
            "actionRatios" : {
                  "simpleInsert" : 0,
                  "randomDelete" : 0,
                  "randomRead" : 0,
                  "randomUpdate" : 0,
                  "bulkInsert" : 1
                    }                   
            }
            
        # create workers
        processes = []
        for i in range(self.threads):
            p = Process(target=self.basicCrudWorker, args=(insertedIDs, responseTimes, processStateDone, i, activeThreadCounter, bulkInsertConfig))
            p.start()
            processes.append(p)
        
        log.info("waiting for workers to finish..")
        while all(processStateDone) is False:
            self.data["userCounts"].append({str(dt.datetime.now()): activeThreadCounter.value})
            log.info('tick..')
            time.sleep(5)
        
        while responseTimes.qsize() > 0: # don't use .empty() it lies
            d = responseTimes.get()
            # TODO: how should the timestamp be stashed?
            self.data[d["action"]].append({"ts":d["timestamp"],"v":d["delta_t"]})
        
        #log.info("Terminating and Joining worker threads..")
        #for i in range(self.threads):
        #    #log.debug("terminating Thread %i" % i)
        #    processes[i].terminate()
        #    processes[i].join()
        
        #######################################################
        #
        # CRUD ops
        #
        ###########
        activeThreadCounter = Value("i")
        processStateDone = Array('b',range(self.threads))
        for i in range(self.threads):
            processStateDone[i] = False
            
        # create workers
        #processes = []
        for i in range(self.threads):
            p = Process(target=self.basicCrudWorker, args=(insertedIDs, responseTimes, processStateDone, i, activeThreadCounter, self.benchmarkConfig))
            p.start()
            processes.append(p)
        
        log.info("waiting for workers to finish..")
        while all(processStateDone) is False:
            self.data["userCounts"].append({str(dt.datetime.now()): activeThreadCounter.value})
            log.info('tick..')
            time.sleep(5)
        
        ###################################################
        # NOTE: To work around queue problem, both queues need to be emptied before they are joined
        #        see the "Joining processes that use queues" section here:
        #        https://docs.python.org/2/library/multiprocessing.html#multiprocessing-programming
        ####################
        
        # Sort responseTimes into categories
        log.info("%i response times were collected" % responseTimes.qsize())
        while responseTimes.qsize() > 0: # don't use .empty() it lies
            d = responseTimes.get()
            # TODO: how should the timestamp be stashed?
            self.data[d["action"]].append({"ts":d["timestamp"],"v":d["delta_t"]})
        
        log.info("There should be %i docs in the db" % insertedIDs.qsize())
        while insertedIDs.qsize() > 0:
            _= insertedIDs.get()
        
        log.info("starting to join threads..")
        json.dump(self.data, open("TaskData.json","w"))
        
        log.info("Terminating and Joining worker threads..")
        for i in range(self.threads*2):
            #log.debug("terminating Thread %i" % i)
            processes[i].terminate()
            processes[i].join()

if __name__ == "__main__":
    unittest.main()