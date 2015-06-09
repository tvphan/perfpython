'''
Created on Jun 9, 2015

@author: madmaze
'''
import sys
import datetime as dt
import loremipsum as li

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
        sz=0
        for k in d.keys():
            sz+=len(k)+len(d[k])
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