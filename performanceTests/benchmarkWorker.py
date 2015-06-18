'''
Created on Jun 14, 2015

@author: madmaze
'''
import datetime as dt
import time
import random
from multiprocessing import Queue

# for exceptions
import Queue as Q

class benchmarkWorker(object):
    '''
    classdocs
    '''


    def __init__(self, db, insertedIDs, params=None):
        '''
        Constructor
        '''
        if params is not None:
            self.params = params
        else:
            self.params = {
                    "bulkInsertSize":10
                           }
        self.db = db
        self.insertedIDs = insertedIDs
        self.seqNum = -1
        self.ratios = {
                  "simpleInsert":50,
                  "randomDelete":25,
                  "randomRead":25,
                  "randomUpdate":25,
                  "bulkInsert":5
                  }
        self.actions = []
        
    def getShuffledAction(self):
        if self.actions == []:
            for k in self.ratios:
                self.actions.extend(self.ratios[k]*[k])
            random.seed(time.time())
            for i in range(len(self.actions)/10):
                # lets do a few rounds of suffleing to ensure we 
                # get something actually kinda random
                random.shuffle(self.actions)
            
        return self.actions.pop()
        
    def execRandomAction(self, seqNum):
        self.seqNum = seqNum
        action = self.getShuffledAction()
        
        if action == "simpleInsert":
            return (action, self.execInsert())
        elif action == "randomDelete":
            return (action, self.execDelete())
        elif action == "randomRead":
            return (action, self.execRead())
        elif action == "randomUpdate":
            return (action, self.execUpdate())
        elif action == "bulkInsert":
            return (action, self.execBulkInsert())
        else:
            print "Error, unknown action:", action
        
    def execInsert(self):
        # add a single document
        d = {"_id":"test:"+str(self.seqNum)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
        t = time.time()
        resp = self.db.addDocument(d)
        delta_t = time.time()-t
        if not resp.ok:
            # TODO: report error somehow
            return -1
            pass
        else:
            resp_d = resp.json()
            self.insertedIDs.put({"_id":resp_d['id'],"_rev":resp_d['rev']})
        return delta_t
    
    def execDelete(self):
        ''' Things to note, we are cheating a little, we don't to a read for every delete since we trach the _rev'''
        try:
            d = self.insertedIDs.get_nowait()
            t = time.time()
            resp = self.db.deleteDocument(docID=d['_id'], docRev=d['_rev'])
            delta_t = time.time()-t
            if not resp.ok:
                # TODO: report error somehow
                return -1
                pass
        except Q.Empty:
            return -1
        return delta_t
    
    def execRead(self):
        ''' Read a random read element'''
        try:
            d = self.insertedIDs.get_nowait()
            t = time.time()
            resp = self.db.getDocument(d["_id"])
            delta_t = time.time()-t
            if not resp.ok:
                # TODO: report error somehow
                return -1
                pass
            resp_d = resp.json()
            self.insertedIDs.put({"_id":resp_d['_id'],"_rev":resp_d['_rev']})
        except Q.Empty:
            return -1
        return delta_t
        return -1
    
    def execUpdate(self):
        ''' Update a random element'''
        try:
            d = self.insertedIDs.get_nowait()
            d["lastUpdated"] = str(dt.datetime.now())
            t = time.time()
            resp = self.db.updateDocument(d)
            delta_t = time.time()-t
            if not resp.ok:
                # TODO: report error somehow
                return -1
                pass
            resp_d = resp.json()
            self.insertedIDs.put({"_id":resp_d['id'],"_rev":resp_d['rev']})
        except Q.Empty:
            return -1
        return delta_t
    
    def execBulkInsert(self):
        ''' Bulk inserts'''
        bulkAdd=[]
        for j in range(self.params["bulkInsertSize"]):
            d = {"_id":"test:"+str(self.seqNum)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
            bulkAdd.append(d)
        
        t = time.time()
        resp = self.db.bulkAddDocuments(bulkAdd)
        delta_t = time.time()-t
        if not resp.ok:
            # TODO: report error somehow
            raise Exception("[BulkInsert Error]", resp.status_code)
            pass
        else:
            resp_d = resp.json()
            for d in resp_d:
                self.insertedIDs.put({"_id":d['id'],"_rev":d['rev']})
        return delta_t
            