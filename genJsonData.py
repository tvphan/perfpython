'''
Created on Jun 9, 2015

@author: madmaze
'''
import sys
import datetime as dt
import loremipsum as li
import json
import random
import numpy as np

class genJsonData(object):
    '''
    classdocs
    '''


    def __init__(self, templateFile=None):
        self.templateFile = templateFile
        self.template = None
        
        if self.templateFile is not None:
            self.template = json.load(open(self.templateFile))
    
    def popValue(self,v):
        if isinstance(v, list):
            for n,_ in enumerate(v):
                v[n] = self.popValue(v[n])
        elif isinstance(v, dict):
            for k in v:
                v[k] = self.popValue(v[k])
        elif (isinstance(v,unicode) or isinstance(v,str)) and v[0]=="[" and v[-1]=="]":
            if isinstance(v,unicode):
                v = str(v)
            
            # strip out [ and ]
            v = v[1:-1]
            # match brackets for recursive gen v.count("[") == v.count("]"):
            bits = v.split("|")
            # expecting [<type>|<value/parameter>]
            if bits[0] == "int":
                if bits[1] == "random":
                    v = np.int32(random.randint(-65535,65535))
                else:
                    # attempt to parse given value
                    v = np.int32(bits[1])
            elif bits[0] == "float":
                if bits[1] == "random":
                    v = np.float32(random.uniform(-65535,65535))
                else:
                    # attempt to parse given value
                    v = np.float32(bits[1])
            elif bits[0] == "boolean":
                if bits[1] == "random":
                    v = np.bool8(random.getrandbits(1))
                else:
                    # attempt to parse given value
                    v = np.bool8(bits[1])
            elif bits[0] == "string":
                if "variable" in bits[1]:
                    # TODO: check the its in the right format, variable(n,n)
                    # split out the parameters of the variable, "variable(1,5)" -> int(1),int(5)
                    params = map(int, bits[1].replace("variable(","").replace(")","").split(","))
                    v = self.getText(random.randint(params[0],params[1]))
                elif "fixed" in bits[1]:
                    # TODO check the its in the right format, fixed(n)
                    param = int(bits[1].replace("fixed(","").replace(")",""))
                    v = self.getText(param)
                else:
                    # attempt to use the given value
                    v = bits[1]
                    
            elif bits[0] == "none" or bits[0] == "null":
                v = None
            
            
        else:
            print "invalid template, got hung up on: ", v, type(v)
        return v

    def genJsonFromTemplate(self):
        if self.template is not None:
            for k in self.template:
                self.template[k] = self.popValue(self.template[k])
            return self.template
        else:
            return None

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
    gen = genJsonData(templateFile="templates/basic_template.json")
    print gen.genJsonFromTemplate()