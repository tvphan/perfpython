#!/usr/bin/env python
##################################################################
# Licensed Materials - Property of IBM
# (c) Copyright IBM Corporation 2015. All Rights Reserved.
# 
# Note to U.S. Government Users Restricted Rights:  Use,
# duplication or disclosure restricted by GSA ADP Schedule 
# Contract with IBM Corp.
##################################################################
'''
Created on Jul 29, 2015

@author: madmaze
'''
import benchmarkDriver.genericBenchmarkDriver as driver
import pyCloudantDB.pyCloudantDB as cdb
import config as c
import unittest
import logging
import benchmarkWorker as bW
import benchmark_test_lucene_queries as bW_lucene
import sys
import time

class cloudantBenchmarkDriver(driver.genericBenchmarkDriver, unittest.TestCase):
    '''
    Simple Cloudant Benchmark, randomly execute basic CRUD ops
    
    This benchmark is configured through config.py
    '''
        
    def setUp(self):
        ''' First do generic setup, then setup benchmark specific components '''
        
        # Call the standard setup
        super(cloudantBenchmarkDriver, self).setUp(c)
        
        # Setup Database connection
        self.db = cdb.pyCloudantDB(self.benchmarkConfig["dbConfig"])
        
        # Test Database connection
        respConn = self.db.testConnection()
        if not respConn.ok:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
        
        # Capture Database version/build
        self.dbVersion = respConn.json()
        self.taskDataObject["info"]["dbVersion"] = self.dbVersion
        
        # Hide password in taskDataObject
        # Recursively step though the dict and hide any "auth"-tuples
        def hidePassword(tdObj):
            if isinstance(tdObj, dict):
                for k in tdObj:
                    if k == "auth" and isinstance(tdObj[k], tuple):
                        usr,pw = tdObj[k]
                        tdObj[k] = (usr,"***")
                    else:
                        tdObj[k] = hidePassword(tdObj[k])
            return tdObj
            
        self.taskDataObject["info"] = hidePassword(self.taskDataObject["info"])
        
            
        # Add Database for testing
        respAdd = self.db.addDatabase(self.benchmarkConfig["dbConfig"]["dbname"], deleteIfExists=True)
        if not respAdd.ok:
            self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
        
        # Populate expected tasks
        self.testName = "MultiThreadedBenchmark"
        
        
    def tearDown(self):
        ''' First do generic tearDown, then clean up cloudant db generated during benchmark '''
        super(cloudantBenchmarkDriver, self).tearDown()
        
        # Remove Database after test completion
        respDel = self.db.deleteDatabase(self.benchmarkConfig["dbConfig"]["dbname"])
        if not respDel.ok:
            self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))
            
    def threadWorker_preStage(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, benchmarkConfig, idPool):
        ''' This preStage is intended to populate the database with some documents before we test '''

        # assemble database population (bulk insert) config
        bulkInsertConfig = {
            "templateFile" : "templates/iron_template.json",
            "concurrentThreads" : benchmarkConfig["concurrentThreads"],
            "iterationPerThread" : benchmarkConfig["bulkInsertsPerThread"],
            "bulkInsertSize" : benchmarkConfig["bulkInsertSize"],
            "actionRatios" : {
                  "simpleInsert" : 0,
                  "randomDelete" : 0,
                  "randomRead" : 0,
                  "randomUpdate" : 0,
                  "bulkInsert" : 1
                    },
            "dbConfig": benchmarkConfig["dbConfig"],
            "maxReqPerSec" : benchmarkConfig["maxReqPerSec"] if "maxReqPerSec" in benchmarkConfig else 0
            }
        self.threadWorker_mainStage(responseTimes, processStateDone, idx, pid, activeThreadCounter, bulkInsertConfig, idPool)
        
    def threadWorker_mainStage_SkipLB(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, benchmarkConfig, idPool):
        ''' This stage is intended to get a small number datapoints circumventing the Load Balancer, in our tests we've noted that
            these are very consistent (low variability) metrics to measure the response times of certain CRUD ops'''
        
        # assemble custom configuration
        noLbBenchmarkConfig = {
            "templateFile" : "templates/iron_template.json",
            "concurrentThreads" : benchmarkConfig["concurrentThreads"],
            "iterationPerThread" : benchmarkConfig["noLbIterationsPerThread"],
            "actionRatios" : {
                  "noLB_simpleInsert" : 1,
                  "noLB_randomDelete" : 1,
                  "noLB_randomRead" : 1,
                  "noLB_randomUpdate" : 1,
                  "noLB_bulkInsert" : 0
                    },
            "dbConfig": benchmarkConfig["noLbDbConfig"],
            "maxReqPerSec" : benchmarkConfig["maxReqPerSec"] if "maxReqPerSec" in benchmarkConfig else 0
            }
        self.threadWorker_mainStage(responseTimes, processStateDone, idx, pid, activeThreadCounter, noLbBenchmarkConfig, idPool)
    
    def threadWorker_mainStage_lucene_queries(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, benchmarkConfig, idPool):
        ''' This stage is a first stab at calling out to the cloudant testy functional tests'''
        
        # assemble custom configuration
        luceneQueriesConfig = {
            "templateFile" : "templates/iron_template.json",
            "concurrentThreads" : benchmarkConfig["concurrentThreads"],
            "iterationPerThread" : benchmarkConfig["iterationPerThread"],
            # TODO: after refactoring allow passing through of custom ratios
            "actionRatios" : None, # Populated in test class
            "dbConfig": benchmarkConfig["dbConfig"],
            "maxReqPerSec" : benchmarkConfig["maxReqPerSec"] if "maxReqPerSec" in benchmarkConfig else 0
            }
        worker = bW_lucene.benchmark_test_lucene_queries(None, idPool, params=luceneQueriesConfig)
        self.threadWorker_mainStage(responseTimes, processStateDone, idx, pid, activeThreadCounter, luceneQueriesConfig, idPool, worker=worker)
        
    def threadWorker_mainStage(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, benchmarkConfig, idPool, worker=None):
        ''' Overrides the generic threadWorker, an instance of this function is executed in each driver thread'''
        
        log = logging.getLogger('mtbenchmark')
        
        if worker is None:
            # Create a local DB object
            db = cdb.pyCloudantDB(benchmarkConfig["dbConfig"])
        
            # Create a local Worker
            worker = bW.benchmarkWorker(db, idPool, params=benchmarkConfig)
        
        # Rate-limiting timer
        lastLoopTime = time.time()
        
        if "maxReqPerSec" in benchmarkConfig and benchmarkConfig["maxReqPerSec"] > 0:
            # setting the maximum requests per second
            minLoopTime = 1.0/benchmarkConfig["maxReqPerSec"]
        else:
            # infinite
            minLoopTime = 0
        
        for i in range(benchmarkConfig["iterationPerThread"]):
            try:
                # TODO: add feature to allow exiting of all threads
                #if any(processStateDone):
                #    print pid, "error on other thread, exiting"
                #    return False
                while (time.time()-lastLoopTime) < minLoopTime:
                    time.sleep(0.01)
                
                # reset timer
                lastLoopTime = time.time()
                
                # Run worker 
                resp = worker.execRandomAction(str(pid)+":"+str(i))                
                
                if "err" in resp.keys() and resp["err"] is True:
                    log.error("("+str(pid)+") Task Level Error: " + resp["action"] + " - Exception: " + resp["msg"])
                
                # Stash response time
                responseTimes.put(resp)
            
            except Exception as e:
                # catch task level exception to prevent early exiting
                e_info = sys.exc_info()[0]
                errLine = "("+str(pid)+") Task Level Error - Exception: "+ str(e_info)
                log.error(errLine)
        
    def testMultiThreadedBenchmark(self):
        log = logging.getLogger('mtbenchmark')
        
        threadWorkers = []
        if "workerStages" not in c.config:
            raise Exception("Failed to find identify stages to be run, 'workerStages' is missing from the config")
        
        # Translate string function names into function pointers
        for worker in c.config["workerStages"]:
            threadWorkers.append(getattr(self, worker))
            log.debug("Matched '%s' to function" % worker)
        self._testMultiThreadedBenchmark(threadWorkers)

if __name__ == "__main__":
    unittest.main()
    
        