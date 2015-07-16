##################################################################
# Licensed Materials - Property of IBM
# (c) Copyright IBM Corporation 2015. All Rights Reserved.
# 
# Note to U.S. Government Users Restricted Rights:  Use,
# duplication or disclosure restricted by GSA ADP Schedule 
# Contract with IBM Corp.
##################################################################
'''
Created on Jun 2, 2015

@author: madmaze
'''
import unittest
import pyCloudantDB.pyCloudantDB as cdb
import config as c
import datetime as dt
import time
import json
import random


class TestBasicCrudOps(unittest.TestCase):
    """ Basic CRUD benchmark """

    def setUp(self):
        self.randomIDs = None
        self.startTime = time.time()
        self.db = cdb.pyCloudantDB(c.config["dbConfig"])
        # test connection
        respConn = self.db.testConnection()
        if not respConn:
            self.assertTrue(respConn,"Failed to successfully connect to Database")
            
        # add database for test
        respAdd = self.db.addDatabase(c.config["dbConfig"]["dbname"])
        if not respAdd.ok:
            self.assertTrue(respAdd.ok,"Failed to successfully add a Database")
            
    def tearDown(self):
        # dump test data
        print "Total "+self.testName+" run time:", time.time()-self.startTime
        json.dump(self.data, open("TaskData.json","w"))
        
        # Remove Database after test completion
        respDel = self.db.deleteDatabase(c.config["dbConfig"]["dbname"])
        if not respDel.ok:
            self.assertTrue(respDel.ok,"Failed to delete Database: " + str(respDel.json()))
            
    def testBasicCrudOps(self):
        self.testName = "BasicCrudOps"
        self.insertedIDs = []
        inserts = 500
        bulkInserts = 500
        bulkInsertSize = 10
        randomReads = 500
        randomUpdates = 500
        randomDeletes = 500
        
        
        self.data = {"simpleInsert":[],
                     "bulkInsert":[],
                     "randomRead":[],
                     "randomUpdate":[],
                     "randomDelete":[]
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
            resp = self.db.addDocument(d)
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
            resp = self.db.bulkAddDocuments(bulkAdd)
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
            resp = self.db.getDocument( self.getRandomDocID() )
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to get document from database: " + str(resp.json()))
            else:
                self.data["randomRead"].append(delta_t)
        
        ########################################
        # Random Update
        #####
        print "starting Random Updates"
        for i in range(randomUpdates):
            # get a random document and update the "lastUpdate" field
            t = time.time()
            resp = self.db.getDocument( self.getRandomDocID() )
            delta_t = time.time()-t
            d = resp.json()
            d["lastUpdated"]=str(dt.datetime.now())
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to get document from database: " + str(resp.json()))
            else:
                self.data["randomRead"].append(delta_t)
            
            # get the document to get a matching _rev id
            t = time.time()
            resp = self.db.updateDocument(d)
            delta_t = time.time()-t
            
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to update document: " + str(resp.json()))
            else:
                self.data["randomUpdate"].append(delta_t)
                
        ########################################
        # Random Deletes
        #####
        print "starting Random Deletes"
        for i in range(randomDeletes):
            # get a random document to fetch the _rev
            t = time.time()
            resp = self.db.getDocument( self.getRandomDocID() )
            delta_t = time.time()-t
            d = resp.json()
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to get document from database: " + str(resp.json()))
            else:
                self.data["randomRead"].append(delta_t)
                
            # get a random document and delete it
            t = time.time()
            resp = self.db.deleteDocument(d['_id'], d['_rev'])
            delta_t = time.time()-t
            if not resp.ok:
                self.assertTrue(resp.ok,"Failed to delete document from database: " + str(resp.json()))
            else:
                self.data["randomDelete"].append(delta_t)
        
    def getRandomDocID(self):
        """ return a random ID from the shuffled deck, if the deck is empty, reshuffle """
        if self.randomIDs is None or self.randomIDs == []:
            self.randomIDs = self.insertedIDs[:]
            random.shuffle(self.randomIDs)
        return self.randomIDs.pop()
        
if __name__ == "__main__":
    unittest.main()