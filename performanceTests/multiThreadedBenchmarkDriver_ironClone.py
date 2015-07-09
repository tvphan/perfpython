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
import requests
import sys
from multiprocessing import Process, Queue, Value, Array
import benchmarkWorker as bW

profile = False

if profile:
    import cProfile
    from pstats import Stats

class TestMultiThreadedDriver(unittest.TestCase):
    """ Basic Multithreaded benchmark """

    def setUp(self):
        
        self.randomIDs = None
        self.startTime = time.time()
        self.benchmarkConfig={
            "templateFile" : "templates/iron_template.json",
            "concurrentThreads" : 10,#0,
            "bulkInsertsPerThread" : 20,
            "bulkInsertSize" : 100,#0,
            "iterationPerThread" : 10,#00,
            "actionRatios" : {
                  "simpleInsert" : 2,
                  "randomDelete" : 3,
                  "randomRead" : 2,
                  "randomUpdate" : 3,
                  "bulkInsert" : 0
                    }                   
            }
        
        if profile:
            self.pr = cProfile.Profile()
            self.pr.enable()
            
        self.threads = self.benchmarkConfig["concurrentThreads"]
        self.runLength = self.benchmarkConfig["iterationPerThread"]
        
        self.db = cdb.pyCloudantDB(c.config["dbConfig"])
        
        # test connection
        # TODO: capture the database version/build for output info
        respConn = self.db.testConnection()
        if not respConn.ok:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
        self.dbVersion = respConn.json()
        
        self.taskDataObject = {
                          "data":{},
                          "info":{
                                  "benchmarkConfig":self.benchmarkConfig,
                                  "dbVersion":self.dbVersion
                                  }
                          }
        
        # just delete the old DB in case it already exists
        # TODO: do a check here to check whether is exists or not
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
        json.dump(self.taskDataObject, open("TaskData.json","w"))
        
        if profile:
            p = Stats(self.pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.reverse_order()
            p.print_stats()
        
        # Remove Database after test completion
        #respDel = self.db.deleteDatabase(c.config["dbConfig"]["dbname"])
        #if not respDel.ok:
        #    self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))

    def basicCrudWorker(self, insertedIDs, responseTimes, processStateDone, idx, pid, activeThreadCounter, benchmarkConfig, session):
        ''' An instance of this is executed in every thread '''
        log = logging.getLogger('mtbenchmark')
        
        # increment out active thread count
        with activeThreadCounter.get_lock():
            activeThreadCounter.value += 1
            
        log.info("pid:%i started.." % pid)
        try:
            # Create new requests session
            #session = requests.Session()
            
            # Create a local DB object
            db = cdb.pyCloudantDB(config=c.config["dbConfig"], session=session)
            
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
                    #log.debug("pid:%i finished task %i" % (pid,i))
                
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
        
        log.debug("pid:%i about to set State" % pid)
        processStateDone[idx]=True
        log.debug("pid:%i about to decrement activeThreadCnt" % pid)
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
        log.addHandler(logStreamHandler)
        
        logFile = open("./run.log","w")
        logFileHandler = logging.StreamHandler(logFile)
        logFileHandler.setLevel(logging.DEBUG)
        logFileHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log.addHandler(logFileHandler)
        
        
        self.testName = "MultiThreadedBenchmark"
        self.taskDataObject["data"] = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[],
                     "randomDelete":[],
                     "userCounts":[]
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
            "templateFile" : "templates/iron_template.json",
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
        session = requests.Session()
        session.auth = c.config["dbConfig"]["auth"]
        # create workers
        processes = []
        for i in range(self.threads):
            p = Process(target=self.basicCrudWorker, args=(insertedIDs, responseTimes, processStateDone, i, i, activeThreadCounter, bulkInsertConfig, session))
            p.start()
            processes.append(p)
        
        log.info("waiting for workers to finish..")
        while all(processStateDone) is False:
            activeWorkers = activeThreadCounter.value
            self.taskDataObject["data"]["userCounts"].append({"ts":str(dt.datetime.now()),"v":activeWorkers})
            log.info('tick.. %d active workers' % activeWorkers)
            time.sleep(5)
        
        log.info("%i response times were collected" % responseTimes.qsize())
        while responseTimes.qsize() > 0: # don't use .empty() it lies
            d = responseTimes.get()
            # TODO: how should the timestamp be stashed?
            self.taskDataObject["data"][d["action"]].append({"ts":d["timestamp"],"v":d["delta_t"]})
            
        # Lets not forcefully end the first set of threads in case they are still
        #  messing around with the queue
        
        #######################################################
        #
        # CRUD ops
        #
        ###########
        activeThreadCounter = Value("i")
        processStateDone2 = Array('b',range(self.threads))
        for i in range(self.threads):
            processStateDone[i] = False
            
        # create workers
        for i in range(self.threads):
            p = Process(target=self.basicCrudWorker, args=(insertedIDs, responseTimes, processStateDone2, i, self.threads+i, activeThreadCounter, self.benchmarkConfig, session))
            p.start()
            processes.append(p)
        
        log.info("waiting for workers to finish..")
        while all(processStateDone2) is False:
            activeWorkers = activeThreadCounter.value
            self.taskDataObject["data"]["userCounts"].append({"ts":str(dt.datetime.now()),"v":activeWorkers})
            log.info('tick.. %d active workers' % activeWorkers)
            time.sleep(5)
        
        ###################################################
        # NOTE: To work around queue problem, both queues need to be emptied before they are joined
        #        see the "Joining processes that use queues" section here:
        #        https://docs.python.org/2/library/multiprocessing.html#multiprocessing-programming
        ####################
        
        # Sort responseTimes into categories
        log.info("an additional %i response times were collected" % responseTimes.qsize())
        while responseTimes.qsize() > 0: # don't use .empty() it lies
            d = responseTimes.get()
            # TODO: how should the timestamp be stashed?
            self.taskDataObject["data"][d["action"]].append({"ts":d["timestamp"],"v":d["delta_t"]})
        
        log.info("There should be %i docs in the db" % insertedIDs.qsize())
        while insertedIDs.qsize() > 0:
            _= insertedIDs.get()
        
        log.info("starting to join threads..")
        
        json.dump(self.taskDataObject, open("TaskData.json","w"))
        
        log.info("Terminating and Joining worker threads..")
        for i in range(self.threads*2):
            processes[i].terminate()
            processes[i].join()

if __name__ == "__main__":
    unittest.main()