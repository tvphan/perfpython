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
import sys

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
        self.db = cdb.pyCloudantDB(c.config["dbConfig"])
        
        # Test Database connection
        respConn = self.db.testConnection()
        if not respConn.ok:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
        
        # Capture Database version/build
        self.dbVersion = respConn.json()
        self.taskDataObject["dbVersion"]=self.dbVersion
            
        # Add Database for testing
        respAdd = self.db.addDatabase(c.config["dbConfig"]["dbname"], deleteIfExists=True)
        if not respAdd.ok:
            self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
        
        # Populate expected tasks
        self.taskDataObject["data"] = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[],
                     "randomDelete":[],
                     "userCounts":[]
                     }
        self.testName = "MultiThreadedBenchmark"
        
        
    def tearDown(self):
        ''' First do generic tearDown, then clean up cloudant db generated during benchmark '''
        super(cloudantBenchmarkDriver, self).tearDown()
        
        # Remove Database after test completion
        respDel = self.db.deleteDatabase(c.config["dbConfig"]["dbname"])
        if not respDel.ok:
            self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))
        
    def threadWorker(self, responseTimes, processStateDone, pid, activeThreadCounter, benchmarkConfig, idPool):
        ''' Overrides the generic threadWorker, an instance of this function is executed in each driver thread'''
        
        log = logging.getLogger('mtbenchmark')
        
        # Create a local DB object
        db = cdb.pyCloudantDB(c.config["dbConfig"])
        
        # Create a local Worker
        worker = bW.benchmarkWorker(db, idPool, params=benchmarkConfig)
        
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
                responseTimes.put(resp)
            
            except Exception as e:
                # catch task level exception to prevent early exiting
                e_info = sys.exc_info()[0]
                errLine = "("+str(pid)+") Task Level Error - Exception: "+ str(e_info) + " trace:" + str(traceback.format_exc())
                log.error(errLine)
        
    #def testMultiThreadedBenchmark(self):
    #    print("testMultiThreadedBenchmark")
    #    super(cloudant).testMultiThreadedBenchmark()

if __name__ == "__main__":
    unittest.main()
    
        