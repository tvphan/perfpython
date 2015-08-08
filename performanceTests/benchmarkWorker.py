'''
Created on Jun 14, 2015

@author: madmaze
'''
import datetime as dt
import time
import random
from multiprocessing import Queue
import logging
import genJsonData as gen

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
        self.db = db
        self.insertedIDs = insertedIDs
        self.seqNum = -1
        
        if params is not None and "templateFile" in params:
            templateFile = params["templateFile"]
        else:
            templateFile = "templates/basic_template.json"
        self.gen = gen.genJsonData(templateFile=templateFile)
        
        if params is not None and "actionRatios" in params:
            self.ratios = params["actionRatios"]
            self.params = params
        else:
            log = logging.getLogger('mtbenchmark')
            log.error("params have not been set, using fallback")
            self.ratios = {
                  "simpleInsert" : 1,
                  "randomDelete" : 1,
                  "randomRead" : 1,
                  "randomUpdate" : 1,
                  "bulkInsert" : 1
                  }
            self.params = {
                    "bulkInsertSize" : 10
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
        # TODO: not so random right now.. 
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
        
        # Partial match the named actions
        if "simpleInsert" in action:
            return self.execInsert(action)
        
        elif "randomDelete" in action:
            return self.execDelete(action)
        
        elif "randomRead" in action:
            return self.execRead(action)
        
        elif "randomUpdate" in action:
            return self.execUpdate(action)
        
        elif "bulkInsert" in action:
            return self.execBulkInsert(action)
        
        else:
            raise Exception({"action":action, "err":True, "msg":"Error, unknown action"})
        
    def execInsert(self, actionName):
        ''' Insert a random document '''
        # Generate a random doc from template
        d = self.gen.genJsonFromTemplate()
        
        d["_id"] = "test:"+str(self.seqNum)
        t = time.time()
        resp = self.db.addDocument(d)
        delta_t = time.time()-t
        tstamp=str(dt.datetime.fromtimestamp(t))
        if not resp.ok:
            return {"action":actionName,
                    "delta_t":-2,
                    "err":True,
                    "msg":"[execInsert Error] "+str(resp.status_code),
                    "timestamp":tstamp}
            
        else:
            resp_d = resp.json()
            d["_rev"]=resp_d["rev"]
            self.insertedIDs.put(d)
            
        return {"action":actionName,
                "delta_t":delta_t,
                "timestamp":tstamp}
    
    def execDelete(self, actionName):
        ''' Things to note, we are cheating a little, we don't to a read for every delete since we trach the _rev'''
        try:
            d = self.getRandomID()
            t = time.time()
            resp = self.db.deleteDocument(docID=d['_id'], docRev=d['_rev'])
            delta_t = time.time()-t
            tstamp=str(dt.datetime.fromtimestamp(t))
            if not resp.ok:
                return {"action":actionName,
                        "delta_t":-2,
                        "err":True,
                        "msg":"[execDelete Error] "+str(resp.status_code),
                        "timestamp":tstamp}
                
        except Q.Empty:
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"[execDelete Error] nothing to process QSize="+str(self.insertedIDs.qsize()),
                    "timestamp":str(dt.datetime.now())}
            
        return {"action":actionName,
                "delta_t":delta_t,
                "timestamp":tstamp}
    
    def execRead(self, actionName):
        ''' Read a random read element'''
        try:
            d = self.getRandomID()
            t = time.time()
            resp = self.db.getDocument(d["_id"])
            delta_t = time.time()-t
            tstamp=str(dt.datetime.fromtimestamp(t))
            if not resp.ok:
                return {"action":actionName,
                        "delta_t":-2,
                        "err":True,
                        "msg":"[execRead Error] "+str(resp.status_code),
                        "timestamp":tstamp}
                
            resp_d = resp.json()
            self.insertedIDs.put(resp_d)
            
        except Q.Empty:
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"[execRead Error] nothing to process QSize="+str(self.insertedIDs.qsize()),
                    "timestamp":str(dt.datetime.now())}
            
        return {"action":actionName,
                "delta_t":delta_t,
                "timestamp":tstamp}
    
    def execUpdate(self, actionName):
        ''' Update a random element'''
        try:
            d = self.getRandomID()
            # execute a random change
            d_changed = self.gen.genRandomChanges(d, 1)
            t = time.time()
            resp = self.db.updateDocument(d_changed)
            delta_t = time.time()-t
            tstamp=str(dt.datetime.fromtimestamp(t))
            if not resp.ok:
                return {"action":actionName,
                        "delta_t":-2,
                        "err":True,
                        "msg":"[execUpdate Error] "+str(resp.status_code),
                        "timestamp":tstamp}
                
            resp_d = resp.json()
            d_changed["_rev"]=resp_d["rev"]
            self.insertedIDs.put(d_changed)
            
        except Q.Empty:
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"[execUpdate Error] nothing to process QSize="+str(self.insertedIDs.qsize()),
                    "timestamp":str(dt.datetime.now())}
            
        return {"action":actionName,
                "delta_t":delta_t,
                "timestamp":tstamp}
    
    def execBulkInsert(self, actionName):
        ''' Bulk inserts a a bunch of random documents, insertSize = params["bulkInsertSize"]'''
        bulkAdd={}
        for j in range(0,self.params["bulkInsertSize"]):
            # Generate a random doc from template
            d = self.gen.genJsonFromTemplate()
            
            d["_id"]="test:"+str(self.seqNum)+":"+str(j)
            bulkAdd[d["_id"]]=d
        
        t = time.time()
        resp = self.db.bulkAddDocuments(bulkAdd.values())
        delta_t = time.time()-t
        tstamp=str(dt.datetime.fromtimestamp(t))
        if not resp.ok:
            return {"action":actionName,
                    "delta_t":-2,
                    "err":True,
                    "msg":"[execBulkInsert Error] "+str(resp.status_code),
                    "timestamp":tstamp}
        else:
            resp_d = resp.json()
            for d in resp_d:
                bulkAdd[d["id"]]["_rev"]=d['rev']
                self.insertedIDs.put(bulkAdd[d["id"]])
                
        return {"action":actionName,
                "delta_t":delta_t,
                "timestamp":tstamp}
            