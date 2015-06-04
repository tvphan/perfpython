'''
Created on Jun 2, 2015

@author: madmaze
'''
import unittest
import cloudantWrapper as cdb
import config as c
import datetime as dt
import time
import json
import random


class TestBasicCrudOps(unittest.TestCase):
    """ quick check to make sure we can connect to cloudant and add/delete a DB """

    def setUp(self):
        self.randomIDs = None
        self.startTime = time.time()
        self.db = cdb.cloudantWrapper(c.config)
        # test connection
        respConn = self.db.testConnection()
        if not respConn:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
            
        # add database for test
        respAdd = self.db.addDatabase(c.config["dbname"], checkResp=False)
        if not respAdd.ok:
            self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
            
    def tearDown(self):
        # dump test data
        print "Total "+self.testName+" run time:", time.time()-self.startTime
        json.dump(self.data, open("TaskData.json","w"))
        
        # Remove Database after test completion
        respDel = self.db.deleteDatabase(c.config["dbname"], checkResp=False)
        if not respDel.ok:
            self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))
            
    def testBasicCrudOps(self):
        self.testName = "BasicCrudOps"
        self.insertedIDs = []
        inserts = 500
        bulkInserts = 500
        bulkInsertSize = 10
        randomReads = 500
        randomUpdate = 500
        
        self.data = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[]
                     }
        
        ########################################
        # Inserts
        #####
        print "starting Inserts"
        for i in range(inserts):
            # add a single document
            d = {"_id":"test:"+str(i)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
            self.insertedIDs.append(d['_id'])
            t = time.time()
            resp = self.db.addDocument(c.config["dbname"], d, checkResp=False)
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to add document to database: " + str(resp.json()))
            else:
                self.data["simpleInsert"].append(delta_t)
        
        ########################################
        # Bulk Inserts
        #####
        print "starting Bulk Inserts"
        for i in range(bulkInserts):
            # create bulkAdd onject
            bulkAdd=[]
            for j in range(bulkInsertSize):
                d = {"_id":"test:"+str(j)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
                bulkAdd.append(d)
                self.insertedIDs.append(d['_id'])
            
            # insert all items in bulkAdd at once
            t = time.time()
            resp = self.db.bulkAddDocuments(c.config["dbname"], bulkAdd, checkResp=False)
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to add document to database: " + str(resp.json()))
            else:
                self.data["bulkInsert"].append(delta_t)

        ########################################
        # Random Read
        #####
        print "starting Random Reads"
        for i in range(randomReads):
            # retrieve a random document
            t = time.time()
            resp = self.db.getDocument(c.config["dbname"], self.getRandomDocID() )
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to get document from database: " + str(resp.json()))
            else:
                self.data["randomRead"].append(delta_t)
        
        ########################################
        # Random Update
        #####
        print "starting Random Updates"
        for i in range(randomUpdate):
            # get a random document and update the "lastUpdate" field
            t = time.time()
            resp = self.db.getDocument(c.config["dbname"], self.getRandomDocID())
            d = resp.json()
            d["lastUpdated"]=str(dt.datetime.now())
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to get document from database: " + str(resp.json()))
            else:
                self.data["randomRead"].append(delta_t)
            
            # get the document to get a matching _rev id
            t = time.time()
            resp = self.db.updateDocument(c.config["dbname"], d, checkResp=False)
            delta_t = time.time()-t
            
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to update document: " + str(resp.json()))
            else:
                self.data["randomUpdate"].append(delta_t)
        
    def getRandomDocID(self):
        """ return a random ID from the shuffled deck, if the deck is empty, reshuffle """
        if self.randomIDs is None or self.randomIDs == []:
            self.randomIDs = self.insertedIDs[:]
            random.shuffle(self.randomIDs)
        return self.randomIDs.pop()       

    

        
#class TestDeleteDoc(unittest.TestCase):
    """ Delete documents in database 
        - Create 10 docs
        - Delete 10 docs
        - Verify deleted docs are deleted """
"""        
    data={}
    
    def setUp(self):
        self.startTime = time.time()
        self.loops = 10
        self.createdDocs=[]
        self.db = cdb.cloudantWrapper(c.config)
        resp = self.db.addDatabase(c.config["dbname"], checkResp=False)
        if not resp.ok:
            self.assertTrue(resp.ok,"Failed to add Database: " + str(resp.json()))
        
        # create a number of simple documents to deleted during the test
        for i in range(self.loops):
            d={"_id":"test:"+str(i)+":"+str(dt.datetime.now())}
            resp = self.db.addDocument(c.config["dbname"], d, checkResp=False)
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to add document to database: " + str(resp.json()))
            self.createdDocs.append(d['_id'])
    
    def tearDown(self):
        # dump test data
        print "Total "+self.testName+" run time:", time.time()-self.startTime
        json.dump(self.data, open("TaskData_deleteDocs.json","w"))
        
        resp = self.db.deleteDatabase(c.config["dbname"], checkResp=False)
        if not resp.ok:
            self.assertTrue(resp.ok,"Failed to delete Database: " + str(resp.json()))
        
    def testDeleteDocs(self):
        respTimes = []
        self.testName = "DeleteDocs"
        for i in range(len(self.createdDocs)):
            # retrieve document to get the _rev id
            resp = self.db.getDocument(c.config["dbname"], self.createdDocs[i])
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to get _rev for documents from database: " + str(resp.json()))
            rev = resp.json()['_rev']
            
            # delete each document we created during setup
            t = time.time()
            resp = self.db.deleteDocument(c.config["dbname"], self.createdDocs[i], docRev=rev, checkResp=False)
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to delete documents from database: " + str(resp.json()))
            
            # requery the database to verify the document has been deleted
            resp = self.db.getDocument(c.config["dbname"], self.createdDocs[i], checkResp=False)
            if resp.ok:
                self.assertTrue(False,"Failed to delete documents from database: " + str(resp.json()))
            respTimes.append(delta_t)
        
        self.data[self.testName]={"loops":len(self.createdDocs),"responseTimes":respTimes}
        self.assertTrue(True,"Failed to delete document from database: " + str(resp.json())) """
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()