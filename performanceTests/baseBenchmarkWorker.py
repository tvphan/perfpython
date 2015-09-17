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
        
    def addActions(self, newActions):
        if not isinstance(newActions, dict):
            raise "newActions is not a dictionary"
        self.actionTable = dict(self.actionTable, **newActions)

    def addRatios(self, newRatios):
        if not isinstance(newRatios, dict):
            raise "newActions is not a dictionary"
        self.actions = dict(self.actions, **newRatios)

    def timeStart(self): #TODO: Should be part of base class
        """
        Set or reset starting time
        """
        self.tStart = time.time()
        self.tEnd = 0.0
        
    def timeEnd(self): #TODO: Should be part of base class
        """
        Calculate elapsed time if not already set
        """
        if self.tEnd is 0.0:
            self.delta_t = time.time()-self.tStart
            self.tstamp=str(dt.datetime.fromtimestamp(self.tStart))
        
    def execAction(self, actionName):
        """
        Executes test method
        * provides default time management - timeStart() and timeEnd() methods which can optionally be called to avoid timing significant pre- or post-processing
        * invokes the test method
        * handles bad response complaints
        * catches expected exceptions for things like queue underflow, etc. 
        """
        method = self.actionTable[actionName]
        if method is None:
            raise Exception({"action":actionName, "err":True, "msg":"Error, unknown action"})
        try:
            self.timeStart()
            resp = method(self, actionName)
            self.timeEnd()
        
            if not resp.ok:
                return {"action":actionName,
                        "delta_t":-2,
                        "err":True,
                        "msg":"["+actionName+" Error] "+str(resp.status_code),  #TODO: Which name to use
                        "timestamp":self.tstamp}
            
        except Q.Empty:
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"["+actionName+"] nothing to process QSize="+str(self.insertedIDs.qsize()),  #TODO: Which name to use
                    "timestamp":str(dt.datetime.now())}
            
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            return {"action":actionName,
                    "delta_t":-1,
                    "err":True,
                    "msg":"["+actionName+"] ="+ e,  #TODO: Which name to use
                    "timestamp":str(dt.datetime.now())}
            
        return {"action":actionName,
                "delta_t":self.delta_t,
                "timestamp":self.tstamp}
