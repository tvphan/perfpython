#!/usr/bin/env python
##################################################################
# Licensed Materials - Property of IBM
# (c) Copyright IBM Corporation 2015. All Rights Reserved.
# 
# Note to U.S. Government Users Restricted Rights:  Use,
# duplication or disclosure restricted by GSA ADP Schedule 
# Contract with IBM Corp.
##################################################################

import datetime as dt
import time
import random
from multiprocessing import Queue
import logging as log
import sys

import genJsonData as gen
# for exceptions
import Queue as Q

class baseBenchmarkWorker(object):
    '''
    Base class for benchmarkWorker threads providing
    * time management
    * execution table management and execution
    * exception handling
    '''
    
    def __init__(self, db):
        self.db = db
        self.ratios = {}
        self.actionTable = {}
        self.actions = []
        self.insertedIDs = None  #TODO: What type is insertedIDs ? Should it be in base ? 
        self.seqNum = -1
             
    def addActions(self, newActions):
        if not isinstance(newActions, dict):
            raise "newActions is not a dictionary"
        self.actionTable = dict(self.actionTable, **newActions)

    def addRatios(self, newRatios):
        if not isinstance(newRatios, dict):
            raise "newRatios is not a dictionary"
        self.ratios = dict(self.ratios, **newRatios)

    def timeStart(self):
        """
        Set or reset starting time
        """
        self.tStart = time.time()
        self.tDelta = -1.0
        self.tEnd = 0.0
        self.tStamp = ""
        
    def timeEnd(self):
        """
        Calculate elapsed time if not already set
        """
        if self.tEnd == 0.0:
            self.tEnd = time.time()
            self.tDelta = self.tEnd-self.tStart
            self.tStamp=str(dt.datetime.fromtimestamp(self.tStart))
        
    def getShuffledAction(self):
        if self.actions == []:
            for k in self.ratios:
                self.actions.extend(self.ratios[k]*[k])
            random.seed(time.time())
            for i in range(len(self.actions)/10):
                # lets do a few rounds of shuffling to ensure we 
                # get something actually kinda random
                random.shuffle(self.actions)
            
        return self.actions.pop()
    
    def getRandomID(self):
        # TODO: not so random right now.. 
        t=time.time()
        d = self.insertedIDs.get(timeout=10)  #WHY DOES THIS TAKE ANYTIME AT ALL ???
        delta_t=time.time()-t
        
        if delta_t >1:
            log = log.getLogger('mtbenchmark')
            log.warn("getting Random ID took a long time:"+str(delta_t))
            
        return d
        
    def execRandomAction(self, seqNum):
        self.seqNum = seqNum
        action = self.getShuffledAction()
        return self.execAction(action)
 
    def execAction(self, actionName):
        """
        Executes test method
        * provides default time management - timeStart() and timeEnd() methods which can optionally be called to avoid timing significant pre- or post-processing
        * invokes the test method
        * handles bad response complaints
        * catches expected exceptions for things like queue underflow, etc. 
        """
        if "noLB_" in actionName:
            shortName = actionName.replace("noLB_","")
            method = self.actionTable[shortName]
        else:
            method = self.actionTable[actionName]
            
        if method is None:
            raise Exception({"action":actionName, "err":True, "msg":"Error, unknown action"})
        try:
            self.timeStart()
            resp = method(self)
            self.timeEnd()
        
            if not resp.ok:
                return {"action":actionName,
                        "delta_t":-2,
                        "err":True,
                        "msg":"["+actionName+" Error] "+str(resp.status_code),
                        "timestamp":self.tStamp}
            
        except Q.Empty:
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"["+actionName+"] nothing to process QSize="+str(self.insertedIDs.qsize()), 
                    "timestamp":str(dt.datetime.now())}
            
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"["+actionName+"] ="+ e, 
                    "timestamp":str(dt.datetime.now())}
            
        return {"action":actionName,
                "delta_t":self.tDelta,
                "timestamp":self.tStamp}
