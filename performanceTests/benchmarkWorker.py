'''
Created on Jun 14, 2015

@author: madmaze
'''
import datetime as dt
import time
import random
from multiprocessing import Queue
import logging

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
    
    def getRandomID(self):
        t=time.time()
        d = self.insertedIDs.get(timeout=10)
        delta_t=time.time()-t
        
        if delta_t >1:
            log = logging.getLogger('mtbenchmark')
            log.warn("getting Random ID took a long time:"+str(delta_t))
            
        return d
        
    def execRandomAction(self, seqNum):
        self.seqNum = seqNum
        action = self.getShuffledAction()
        
        if action == "simpleInsert":
            return self.execInsert()
        elif action == "randomDelete":
            return self.execDelete()
        elif action == "randomRead":
            return self.execRead()
        elif action == "randomUpdate":
            return self.execUpdate()
        elif action == "bulkInsert":
            return self.execBulkInsert()
        else:
            raise Exception({"action":action, "err":True, "msg":"Error, unknown action"})
        
    def execInsert(self):
        ''' Insert a random document '''
        # add a single document
        d = {"_id":"test:"+str(self.seqNum)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
        t = time.time()
        resp = self.db.addDocument(d)
        delta_t = time.time()-t
        if not resp.ok:
            return {"action":"simpleInsert","delta_t":-2,"err":True,"msg":"[execInsert Error] "+str(resp.status_code)}
        else:
            resp_d = resp.json()
            self.insertedIDs.put({"_id":resp_d['id'],"_rev":resp_d['rev']})
        return {"action":"simpleInsert","delta_t":delta_t}
    
    def execDelete(self):
        ''' Things to note, we are cheating a little, we don't to a read for every delete since we trach the _rev'''
        try:
            d = self.getRandomID()
            t = time.time()
            resp = self.db.deleteDocument(docID=d['_id'], docRev=d['_rev'])
            delta_t = time.time()-t
            if not resp.ok:
                return {"action":"randomDelete","delta_t":-2,"err":True,"msg":"[execDelete Error] "+str(resp.status_code)}
        except Q.Empty:
            return {"action":"randomDelete","delta_t":-1,"err":True,"msg":"[execDelete Error] nothing to process QSize="+str(self.insertedIDs.qsize())}
        return {"action":"randomDelete","delta_t":delta_t}
    
    def execRead(self):
        ''' Read a random read element'''
        try:
            d = self.getRandomID()
            t = time.time()
            resp = self.db.getDocument(d["_id"])
            delta_t = time.time()-t
            if not resp.ok:
                return {"action":"randomRead","delta_t":-2,"err":True,"msg":"[execRead Error] "+str(resp.status_code)}
            resp_d = resp.json()
            self.insertedIDs.put({"_id":resp_d['_id'],"_rev":resp_d['_rev']})
        except Q.Empty:
            return {"action":"randomRead","delta_t":-1,"err":True,"msg":"[execRead Error] nothing to process QSize="+str(self.insertedIDs.qsize())}
        return {"action":"randomRead","delta_t":delta_t}
    
    def execUpdate(self):
        ''' Update a random element'''
        try:
            d = self.getRandomID()
            d["lastUpdated"] = str(dt.datetime.now())
            t = time.time()
            resp = self.db.updateDocument(d)
            delta_t = time.time()-t
            if not resp.ok:
                return {"action":"randomUpdate","delta_t":-2,"err":True,"msg":"[execUpdate Error] "+str(resp.status_code)}
            resp_d = resp.json()
            self.insertedIDs.put({"_id":resp_d['id'],"_rev":resp_d['rev']})
        except Q.Empty:
            return {"action":"randomUpdate","delta_t":-1,"err":True,"msg":"[execUpdate Error] nothing to process QSize="+str(self.insertedIDs.qsize())}
        return {"action":"randomUpdate","delta_t":delta_t}
    
    def execBulkInsert(self):
        ''' Bulk inserts a a bunch of random documents, insertSize = params["bulkInsertSize"]'''
        bulkAdd=[]
        for j in range(self.params["bulkInsertSize"]):
            d = {"_id":"test:"+str(self.seqNum)+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
            bulkAdd.append(d)
        
        t = time.time()
        resp = self.db.bulkAddDocuments(bulkAdd)
        delta_t = time.time()-t
        if not resp.ok:
            return {"action":"bulkInsert", "delta_t":-2, "err":True, "msg":"[execBulkInsert Error] "+str(resp.status_code)}
        else:
            resp_d = resp.json()
            for d in resp_d:
                self.insertedIDs.put({"_id":d['id'],"_rev":d['rev']})
        return {"action":"bulkInsert","delta_t":delta_t}
            