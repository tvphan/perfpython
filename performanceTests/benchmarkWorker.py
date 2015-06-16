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


    def __init__(self, db, insertedIDs):
        '''
        Constructor
        '''
        self.db = db
        self.insertedIDs = insertedIDs
        self.seqNum = -1
        """self.ratios = {"simpleInsert":50,
                  "randomDelete":10,
                  "randomUpdate":30,
                  "bulkInsert":10}"""
        self.ratios = {"simpleInsert":100,
                  "randomDelete":50,
                  "randomUpdate":0,
                  "bulkInsert":0}
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
        elif action == "randomUpdate":
            return (action, self.execUpdate())
        elif action == "bulkInsert":
            return (action, self.execBulkInsert)
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
            self.insertedIDs.put({"id":resp_d['id'],"rev":resp_d['rev']})
        return delta_t
    
    def execDelete(self):
        ''' Things to note, we are cheating a little, we don't to a read for every delete since we trach the _rev'''
        try:
            d = self.insertedIDs.get_nowait()
            t = time.time()
            resp = self.db.deleteDocument(docID=d['id'], docRev=d['rev'])
            delta_t = time.time()-t
            if not resp.ok:
                # TODO: report error somehow
                return -1
                pass
        except Q.Empty:
            return -1
        return delta_t
    
    def execUpdate(self):
        return 0.0
    
    def execbulkInsert(self):
        return 0.0