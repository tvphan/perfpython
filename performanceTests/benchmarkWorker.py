'''
Created on Jun 14, 2015

@author: madmaze
'''
import datetime as dt
import time
import random

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
                  "randomDelete":0,
                  "randomUpdate":0,
                  "bulkInsert":0}
        self.actions = []
        
    def getShuffledAction(self):
        if self.actions == []:
            for k in self.ratios:
                self.actions.extend(self.ratios[k]*[k])
            random.shuffle(self.actions)
            
        return self.actions.pop()
        
    def execRandomAction(self, seqNum):
        self.seqNum = seqNum
        action = self.getShuffledAction()
        #print action
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
            #self.assertTrue(resp.ok,"Failed to add document to database: " + str(resp.json()))
            # TODO: report error somehow
            pass
        else:
            self.insertedIDs.put(d['_id'])
        return delta_t
    
    def execDelete(self):
        return 0.0
    
    def execUpdate(self):
        return 0.0
    
    def execbulkInsert(self):
        return 0.0