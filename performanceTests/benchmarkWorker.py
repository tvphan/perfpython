#!/usr/bin/env python
##################################################################
# Licensed Materials - Property of IBM
# (c) Copyright IBM Corporation 2015. All Rights Reserved.
# 
# Note to U.S. Government Users Restricted Rights:  Use,
# duplication or disclosure restricted by GSA ADP Schedule 
# Contract with IBM Corp.
##################################################################
'''
Created on Jun 14, 2015

@author: madmaze
'''
import baseBenchmarkWorker as bBW
import logging
import genJsonData as gen

class benchmarkWorker(bBW.baseBenchmarkWorker):
    '''
    classdocs
    '''

    def __init__(self, db, insertedIDs, params=None):
        '''
        Constructor
        '''
        bBW.baseBenchmarkWorker.__init__(self,db)
        
        ###################################
        #TODO: Need general model of some params being in base class, others added by the subclasses
        # self.ratios should be in base and subclass should ADD to it not define

        self.insertedIDs = insertedIDs
        
        if params is not None and "templateFile" in params:
            templateFile = params["templateFile"]
        else:
            templateFile = "templates/basic_template.json"
        self.gen = gen.genJsonData(templateFile=templateFile)
        
        ####################################
        # class-specific
                
        self.addActions({"simpleInsert" : benchmarkWorker.execInsert,
                         "randomDelete" : benchmarkWorker.execDelete,
                         "randomRead"   : benchmarkWorker.execRead,
                         "randomUpdate" : benchmarkWorker.execUpdate,
                         "bulkInsert"   : benchmarkWorker.execBulkInsert
                         })
        
        if params is not None and "actionRatios" in params:
            self.addRatios(params["actionRatios"])
            self.params = params
        else:
            log = logging.getLogger('mtbenchmark')
            log.error("params have not been set, using fallback")
            self.addRatios({
                  "simpleInsert" : 1,
                  "randomDelete" : 1,
                  "randomRead" : 1,
                  "randomUpdate" : 1,
                  "bulkInsert" : 1
                  })
            self.params = {
                    "bulkInsertSize" : 10
                    }
 
    def execInsert(self):
        ''' Insert a random document '''
        # Generate a random doc from template
        d = self.gen.genJsonFromTemplate()
        
        d["_id"] = "test:"+str(self.seqNum)   #TODO: incremental id generator
        self.timeStart()  #Optional, used only to override the default if pre-processing 
        resp = self.db.addDocument(d)
        self.timeEnd() #Optional, used to preset the time if post-processing might take time
        
        # if not resp.ok will be covered on return to report the problem (more consistent)
        #TODO: If resp.ok handling should use standardized methods for 
        if resp.ok:
            resp_d = resp.json()
            d["_rev"]=resp_d["rev"]
            self.insertedIDs.put(d)
        return resp
    
    def execDelete(self):
        ''' Things to note, we are cheating a little, we don't to a read for every delete since we track the _rev'''
        d = self.getRandomID()
        return self.db.deleteDocument(docID=d['_id'], docRev=d['_rev'])
    
    def execRead(self):
        ''' Read a random read element'''
        d = self.getRandomID()
        resp = self.db.getDocument(d["_id"])
        #TODO: Storing response should be standard method
        if resp.ok:
            resp_d = resp.json()
            self.insertedIDs.put(resp_d)
        return resp

    def execUpdate(self):
        ''' Update a random element'''
        d = self.getRandomID()
        # execute a random change
        d_changed = self.gen.genRandomChanges(d, 1)
        self.timeStart() #TODO: Assumes gen op takes significant time
        resp = self.db.updateDocument(d_changed)
        #TODO: Storing response with different rev should be standard method
        if resp.ok:
            resp_d = resp.json()
            d_changed["_rev"]=resp_d["rev"]
            self.insertedIDs.put(d_changed)
        return resp
            
    def execBulkInsert(self):
        ''' Bulk inserts a a bunch of random documents, insertSize = params["bulkInsertSize"]'''
        bulkAdd={}
        for j in range(0,self.params["bulkInsertSize"]):
            # Generate a random doc from template
            d = self.gen.genJsonFromTemplate()
            
            d["_id"]="test:"+str(self.seqNum)+":"+str(j)
            bulkAdd[d["_id"]]=d
        
        self.timeStart()
        resp = self.db.bulkAddDocuments(bulkAdd.values())
        self.timeEnd()
        #TODO: Storing response with different rev should be standard method
        if resp.ok:
            resp_d = resp.json()
            for d in resp_d:
                bulkAdd[d["id"]]["_rev"]=d['rev']
                self.insertedIDs.put(bulkAdd[d["id"]])
        return resp
