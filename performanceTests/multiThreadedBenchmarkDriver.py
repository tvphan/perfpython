'''
Created on Jun 13, 2015

@author: madmaze
'''
import unittest
import pyCloudantDB as cdb
import config as c
import datetime as dt
import time
import json
import random
from multiprocessing import Process, Queue, Value, Array
import benchmarkWorker as bW

class TestMultiThreadedDriver(unittest.TestCase):
    """ Basic Multithreaded benchmark """

    def setUp(self):
        self.randomIDs = None
        self.startTime = time.time()
        self.db = cdb.pyCloudantDB(c.config)
        # test connection
        respConn = self.db.testConnection()
        if not respConn:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
            
        # add database for test
        respAdd = self.db.addDatabase(c.config["dbname"])
        if not respAdd.ok:
            self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
            
    def tearDown(self):
        # dump test data
        print "Total "+self.testName+" run time:", time.time()-self.startTime
        json.dump(self.data, open("TaskData.json","w"))
        
        # Remove Database after test completion
        #respDel = self.db.deleteDatabase(c.config["dbname"])
        #if not respDel.ok:
        #    self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))

    def basicCrudWorker(self, insertedIDs, responseTimes, processStates, pid, runLength):      
        try:
            
            db = cdb.pyCloudantDB(c.config)
            worker = bW.benchmarkWorker(db, insertedIDs)
            for i in range(runLength):
                # make sure we should continue running..
                if not all(processStates):
                    print pid, "error on other thread, exiting"
                    return
                
                #print pid,"starting worker..",i
                action, delta_t = worker.execRandomAction(str(pid)+":"+str(i))
                
                # add a single document
                #d = {"_id":"test:"+str(i)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
                #t = time.time()
                #resp = db.addDocument(c.config["dbname"], d)
                #delta_t = time.time()-t
                #if not resp.ok:
                #    #self.assertTrue(resp.ok,"Failed to add document to database: " + str(resp.json()))
                #    # TODO: report error somehow
                #    pass
                #else:
                #    insertedIDs.put(d['_id'])
                
                responseTimes.put({action:delta_t})
        except:
            processStates=False
            return

    
    def testMultiThreadedBenchmark(self):
        self.testName = "MultiThreadedBenchmark"
        self.data = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[],
                     "randomDelete":[]
                     }
        threads = 1
        runLength = 500
        insertedIDs = Queue()
        responseTimes = Queue()
        processStates = Array('b',range(threads))
        for i in range(threads):
            processStates[i] = True
            
        processes = []
        # create workers
        for i in range(threads):
            p = Process(target=self.basicCrudWorker, args=(insertedIDs, responseTimes, processStates, i, runLength))
            p.start()
            processes.append(p)
        
        # join workers
        for i in range(threads):
            p.join()
        
        while not insertedIDs.empty():
            print insertedIDs.get()
        
        while not responseTimes.empty():
            d = responseTimes.get()
            if "simpleInsert" in d:
                self.data["simpleInsert"].append(d["simpleInsert"])

if __name__ == "__main__":
    unittest.main()