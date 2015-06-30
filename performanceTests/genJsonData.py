'''
Created on Jun 9, 2015

@author: madmaze
'''
import sys
import datetime as dt
import dummyText as txt
import json
import random
import time
import numpy as np

class genJsonData(object):
    '''
    classdocs
    '''


    def __init__(self, templateFile=None):
        self.templateFile = templateFile
        self.template = None
        
        if self.templateFile is not None:
            try:
                self.template = json.load(open(self.templateFile))
            except Exception as e:
                raise Exception("Failed to load JSON template, validate JSON in template file: " + self.templateFile)
    
    def popValue(self,v):
        ''' This function parses and generates data for a JSON template
        These templates are expected to be in valid JSON, wherever a
        generated value is needed, a place holder is inserted. 
        
        Place holders are formatted in the following syntax:
        [<type>|<random/length/value>]
        type => int|float|string|boolean
        random => a random value will be assigned
        length => either 'variable(<min>,<max>)' or 'fixed(<len>)' 
                    these dictate the length of a string, 
                    not valid other types
        value => it will attempt to parse the given value as the specified <type>
        
        example:
        {
            "array1": [
                [
                    "[float|random]",
                    "[float|random]"
                ], 
                {}, 
            ], 
            "boolean1": "[boolean|true]",
            "integer1": "[int|random]", 
            "obj1": {
                "array2": ["[string|variable(10,25)]","[string|variable(10,25)]","[string|variable(10,25)]"], 
                "obj2": {
                    "boolean2": "[boolean|random]"
                }
            },
            "string1": "[string|fixed(10)]"
        }
        
        becomes:
        {
            "array1": [
                [
                    28358.521,
                    -3308.1692
                ], 
                {}, 
            ], 
            "boolean1": "True",
            "integer1": "29257", 
            "obj1": {
                "array2": ['Lorem ipsum dolor', 'Lorem ipsum. Fu', 'Lorem ipsu'], 
                "obj2": {
                    "boolean2": "False"
                }
            },
            "string1": "Lorem ipsu"
        }
        '''
           
        if isinstance(v, list):
            res = []
            for n,_ in enumerate(v):
                res.append(self.popValue(v[n]))
            v = res
        elif isinstance(v, dict):
            res = {}
            for k in v.keys():
                res[k] = self.popValue(v[k])
            v = res
        elif (isinstance(v,unicode) or isinstance(v,str)) and v[0]=="[" and v[-1]=="]":
            if isinstance(v,unicode):
                v = str(v)
            if v.count("[") != v.count("]"):
                raise Exception("unmatched [ ] brackets: "+str(v))
            
            # strip out [ and ]
            v = v[1:-1]
            bits = v.split("|")
            # expecting [<type>|<value/parameter>]
            if bits[0] == "int":
                if bits[1] == "random":
                    v = self.getRandomInt()
                else:
                    # attempt to parse given value
                    v = int(bits[1])
            elif bits[0] == "float":
                if bits[1] == "random":
                    v = self.getRandomFloat()
                else:
                    # attempt to parse given value
                    v = float(bits[1])
            elif bits[0] == "boolean":
                if bits[1] == "random":
                    v = self.getRandomBoolean()
                else:
                    # attempt to parse given value
                    v = bool(bits[1])
            elif bits[0] == "string":
                if "variable" in bits[1]:
                    # TODO: check the its in the right format, variable(n,n)
                    # split out the parameters of the variable, "variable(1,5)" -> int(1),int(5)
                    randMin, randMax = map(int, bits[1].replace("variable(","").replace(")","").split(","))
                    if randMin > randMax:
                        raise  Exception("randMin must be lower than randMax: "+str(v))
                    v = self.getRandomString(randMin,randMax)
                elif "fixed" in bits[1]:
                    # TODO check the its in the right format, fixed(n)
                    param = int(bits[1].replace("fixed(","").replace(")",""))
                    v = self.getText(param)
                elif bits[1] == "random":
                    v = self.getText(random.randint(0,1024))
                else:
                    # attempt to use the given value
                    v = bits[1]
                    
            elif bits[0] == "none" or bits[0] == "null":
                v = None
            
            
        else:
            raise Exception( "invalid template, got hung up on: "+ str(v) +" "+ str(type(v)))
        return v

    def genJsonFromTemplate(self):
        ''' generate a JSON document based on a supplied template
            the outer most shell of the json doc must be a dict.
            for more detailed explaination see popValue()'''
        temp_template = self.template.copy()
        if self.template is not None:
            for k in self.template:
                temp_template[k] = self.popValue(self.template[k])
            return temp_template
        else:
            return None

    def getText(self, textLen):
        retStr=""
        extraLen = textLen
        while len(retStr) < textLen:
            randLine = random.randint(0,len(txt.dummyText)-1)
            lineLen = len(txt.dummyText[randLine])
            randStart = random.randint(0,lineLen-1)
            if randStart + extraLen <= lineLen: 
                retStr += txt.dummyText[randLine][randStart:randStart+extraLen]
            else:
                retStr += txt.dummyText[randLine][randStart:]
            randStart = textLen - len(retStr)
        
        return retStr
    
    def getRandomBoolean(self):
        return bool(random.getrandbits(1))
    
    def getRandomString(self, randMin=6, randMax=60):
        return self.getText(random.randint(randMin,randMax))
    
    def getRandomInt(self):
        return int(random.randint(-65535,65535))
    
    def getRandomFloat(self):
        return float(random.uniform(-65535,65535))
    
    def genRandomChanges(self,d,numChanges):
        # remove id and rev so they don't get changed
        id = d.pop("_id",None)
        rev = d.pop("_rev",None)
        
        d = self.randomlyChange(d,numChanges)
        
        # put _id and _rev back
        if id is not None:
            d["_id"] = id
        if rev is not None:
            d["_rev"] = rev
            
        return d
    
    def randomlyChange(self,d,numChanges):
        """ Takes a json document and recursively makes a number of random changes """
        
        if isinstance(d,dict):
            for c in range(numChanges):
                if len(d.keys())==0:
                    return d
                i = random.randint(0,len(d.keys())-1)
                d[d.keys()[i]] = self.randomlyChange(d[d.keys()[i]],1)
            return d
        elif isinstance(d,list):
            # itereate over the number of changes we want to make
            for c in range(numChanges):
                if len(d)==0:
                    return d
                i = random.randint(0,len(d)-1)
                d[i] = self.randomlyChange(d[i],1)
            return d
        elif isinstance(d, str) or isinstance(d, unicode):
            return self.getRandomString()
        elif isinstance(d, int):
            return self.getRandomInt()
        elif isinstance(d, float):
            return self.getRandomFloat()
        elif isinstance(d, bool):
            return self.getRandomBoolean()
        else:
            return d
    
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
    gen = genJsonData(templateFile="templates/iron_template.json")
    t = time.time()
    for i in range(10):
        d = gen.genJsonFromTemplate()
    print (time.time()-t)/10
    #print gen.genJsonFromTemplate()
    #print gen.randomlyChange(newTemp, 1)
    