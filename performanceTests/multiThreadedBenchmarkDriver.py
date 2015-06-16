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
import sys
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
        print "test finished:", dt.datetime.now()
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
                
                action, delta_t = worker.execRandomAction(str(pid)+":"+str(i))
                responseTimes.put({action:delta_t})
        except Exception as e:
            e_info = sys.exc_info()[0]
            print "Exception", e_info
            processStates=False
            raise e
            return

    
    def testMultiThreadedBenchmark(self):
        self.testName = "MultiThreadedBenchmark"
        self.data = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[],
                     "randomDelete":[]
                     }
        threads = 10
        runLength = 30
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
            processes[i].join()
        
        data=[]
        while not insertedIDs.empty():
            data.append(insertedIDs.get())
        print "there should be", len(data),"docs in the db"
        
        while not responseTimes.empty():
            d = responseTimes.get()
            self.data[d.keys()[0]].append(d[d.keys()[0]])

if __name__ == "__main__":
    unittest.main()