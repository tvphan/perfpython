'''
Created on Jun 9, 2015

@author: madmaze
'''
import sys
import datetime as dt
import loremipsum as li
import json

class genJsonData(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    def getText(self, textLen):
        retStr=""
        while len(retStr) < textLen:
            para = li.get_paragraph(1)
            retStr += para
        
        return retStr[:textLen]
    
    def sizeOfObj(self,d):
        """ Note these sizes are probaly not accurate, but
            at least they will give a general sense of the
            byte size of an object"""
        sz=0
        if isinstance(d,dict):
            for k in d.keys():
                # add size of the key
                sz += len(k)
                # get the size of the element
                sz += self.sizeOfObj(d[k])
        elif isinstance(d,list):
            for val in d:
                # get the size of the element
                sz += self.sizeOfObj(val)
        elif isinstance(d, str):
            # assuming 1byte chars
            sz += len(d)
        elif isinstance(d, int):
            # assuming 4byte ints
            sz += 4
        elif isinstance(d, float):
            # assuming 8byte float32
            sz += 8
        elif isinstance(d, bool):
            # assuming 1byte bool
            sz += 1
        elif isinstance(d, type(None)):
            # assuming 1byte Null/None(pythonic)
            sz += 1
        else:
            print "not sure what the size of this is:", d
            
        return sz
    
    def genData(self,dataSize=None, itr=None):
        if itr is not None:
            itrStr = ":"+str(itr)
        else:
            itrStr = ""
            
        d = {"_id":"test"+itrStr+":"+str(dt.datetime.now()), "lastUpdate":str(dt.datetime.now())}
        if dataSize is not None:
            addSize = dataSize - self.sizeOfObj(d)-len('payload')
            addText = self.getText(addSize)
            d["payload"]=addText
            
        return d

if __name__ == "__main__":
    gen = genJsonData()
    print gen.genData(dataSize=1024)