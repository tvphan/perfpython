#!/usr/bin/env python
##################################################################
# Licensed Materials - Property of IBM
# (c) Copyright IBM Corporation 2015. All Rights Reserved.
# 
# Note to U.S. Government Users Restricted Rights:  Use,
# duplication or disclosure restricted by GSA ADP Schedule 
# Contract with IBM Corp.
##################################################################
import pylab
import json
import numpy as np
import argparse
import shutil
import os

def main(datafile="TaskData.json", outdir="./", overwrite=False):
    data = json.load(open(datafile))["data"]
    humanReadable ={"simpleInsert":"Simple Doc Insert",
         "bulkInsert":"Simple Bulk Doc Insert (10 Docs/Insert)",
         "randomRead":"Simple Random Doc Read",
         "randomUpdate":"Simple Random Doc Update",
         "randomDelete":"Simple Random Doc Delete",
         "userCounts":"Active Users over time"}
    
    if os.path.exists(outdir):
        if overwrite:
            shutil.rmtree(outdir)
        else:
            print("[ERROR] output dir(\"%s\") already exists, use -x to overwrite" % outdir)
            exit()
            
    os.mkdir(outdir)
    
    fname = datafile.split(os.path.sep)[-1]
    shutil.copyfile("styles.css", os.path.join(outdir, "styles.css"))
    html = open(os.path.join(outdir,"index.html"),"w")
    html.write("""
<html>
<head>
<title>Cloudant Performance Report: %s</title>
<link rel="stylesheet" href="styles.css" type="text/css" />
</head>
<body>
<h1>Performance Result: %s</h1>
<table class="graphs">
<tr>
<td>Raw Plot</td>
<td>95th Percentile</td>
</tr>

    """ % (fname,fname))
    for k in humanReadable.keys():
        d = np.array(data[k])
        if len(d)>0:
            html.write("\t\t<tr>\n")
            html.write("\t\t\t<td>\n")
            err = len(d[np.where(d == -1)])
            print k,"empty queue", 100*(float(err)/len(d))
            err = len(d[np.where(d == -2)])
            print k,"error", 100*(float(err)/len(d))
            
            # index just the values
            vals = np.array([ element["v"] for element in d ])

            vals = vals[np.where(vals > 0)]
            
            pylab.plot(vals, label=k)
            pylab.plot([np.mean(vals)]*len(vals), label="mean")
            pylab.plot([np.median(vals)]*len(vals), label="median")
            pylab.xlabel("Test samples")
            pylab.ylabel("Response Time (s)")
            pylab.title(humanReadable[k])
            pylab.legend()
            pylab.ylim([0,np.max(vals)*1.5])
            pylab.savefig(outdir+"/"+k+".png", dpi=200)
            pylab.clf()
            html.write("\t\t\t\t<img src=\""+k+".png\">\n")
            html.write("\t\t\t</td>\n")
            html.write("\t\t\t<td>\n")
            
            p=np.where(vals < np.percentile(vals,95))[0]
            p95th = vals[p]
            pylab.plot(p95th, label=k+"_95th percentile")
            pylab.plot([np.mean(p95th)]*len(p95th), label="mean")
            pylab.plot([np.median(p95th)]*len(p95th), label="median")
            pylab.xlabel("Test samples")
            pylab.ylabel("Response Time (s)")
            pylab.title(humanReadable[k])
            pylab.legend()
            pylab.ylim([0,np.max(p95th)*1.5])
            pylab.savefig(outdir+"/"+k+"_95th.png", dpi=100)
            pylab.clf()
            html.write("\t\t\t\t<img src=\""+k+"_95th.png\">\n")
            html.write("\t\t\t</td>\n")
            html.write("\t\t</tr>\n")
    
    # close up the html
    html.write("""
    </table>
</body>
</html>""")
    html.close()
    print "done generating plots.."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given a TaskData.json, plot basic graphs for each top level item, expected format: {\"<taskname\":[<resp0>,<resp1>,<resp2>,..]}")
    parser.add_argument("--dataFile", dest="dataFile", default="./TaskData.json", help="Input Filename (Default: ./TaskData.json)")
    parser.add_argument("--outputDir", dest="outputDir", default="./plots", help="Output dir (Default: ./plots)")
    parser.add_argument("-x", dest="overwrite", action='store_true', help="Overwrite output dir (Default: False)")
    args = parser.parse_args()
    
    main(args.dataFile, args.outputDir, args.overwrite)
