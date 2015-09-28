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
import BenchmarkWorker_CRUD as CrudBW
import BenchmarkWorker_testy_lucene as LuceneBW
import sys
import time

class cloudantBenchmarkDriver(driver.genericBenchmarkDriver):
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
        
        if "freshDatabase" in self.benchmarkConfig["dbConfig"] and self.benchmarkConfig["dbConfig"]["freshDatabase"] is True:
            # Add Database for testing
            respAdd = self.db.addDatabase(self.benchmarkConfig["dbConfig"]["dbname"], deleteIfExists=True)
            if not respAdd.ok:
                self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
        
        # Populate expected tasks
        self.testName = "MultiThreadedBenchmark"
        
        
    def tearDown(self):
        ''' First do generic tearDown, then clean up cloudant db generated during benchmark '''
        super(cloudantBenchmarkDriver, self).tearDown()
        
        if "cleanupDatabase" in self.benchmarkConfig["dbConfig"] and self.benchmarkConfig["dbConfig"]["cleanupDatabase"] is True:
            # Remove Database after test completion
            respDel = self.db.deleteDatabase(self.benchmarkConfig["dbConfig"]["dbname"])
            if not respDel.ok:
                self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))
            
    def threadWorker_simple_datapop(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool):
        ''' This preStage is intended to populate the database with some documents before we test '''
        
        # TODO: check whether a self.db exists
        # Create a local DB object
        db = cdb.pyCloudantDB(workerConfig["dbConfig"])
    
        # Create a local Worker
        worker = CrudBW.BenchmarkWorker_CRUD(db, idPool, params=workerConfig)
        self.threadWorker_driverLoop(responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool, worker)
        
    def threadWorker_CRUD_SkipLB(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool):
        ''' This stage is intended to get a small number datapoints circumventing the Load Balancer, in our tests we've noted that
            these are very consistent (low variability) metrics to measure the response times of certain CRUD ops'''
        
        # TODO: check whether a self.db exists
        # Create a local DB object
        db = cdb.pyCloudantDB(workerConfig["dbConfig"])
    
        # Create a local Worker
        worker = CrudBW.BenchmarkWorker_CRUD(db, idPool, params=workerConfig)
        self.threadWorker_driverLoop(responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool, worker)
    
    def threadWorker_testy_lucene(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool):
        ''' This stage is a first stab at calling out to the cloudant testy functional tests'''
        
        '''# assemble custom configuration
        luceneQueriesConfig = {
            "templateFile" : "templates/iron_template.json",
            "concurrentThreads" : benchmarkConfig["concurrentThreads"],
            "iterationPerThread" : benchmarkConfig["iterationPerThread"],
            # TODO: after refactoring allow passing through of custom ratios
            "actionRatios" : None, # Populated in test class
            "dbConfig": benchmarkConfig["dbConfig"],
            "maxReqPerSec" : benchmarkConfig["maxReqPerSec"] if "maxReqPerSec" in benchmarkConfig else 0
            }'''
        
        worker = LuceneBW.BenchmarkWorker_testy_lucene(None, idPool, params=workerConfig)
        self.threadWorker_driverLoop(responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool, worker)
        
    def threadWorker_CRUD(self, responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool):
        ''' Overrides the generic threadWorker, an instance of this function is executed in each driver thread'''
        
        log = logging.getLogger('mtbenchmark')
        
        # Create a local DB object
        db = cdb.pyCloudantDB(workerConfig["dbConfig"])
    
        # Create a local Worker
        worker = CrudBW.BenchmarkWorker_CRUD(db, idPool, params=workerConfig)
        self.threadWorker_driverLoop(responseTimes, processStateDone, idx, pid, activeThreadCounter, workerConfig, idPool, worker)
        

if __name__ == "__main__":
    unittest.main()
    
        