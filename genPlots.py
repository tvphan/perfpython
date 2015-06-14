#!/usr/bin/env python
import pylab
import json
import numpy as np
import argparse

def main(datafile="TaskData.json", outdir="./"):
    data = json.load(open(datafile))
    humanReadable ={"simpleInsert":"Simple Doc Insert",
         "bulkInsert":"Simple Bulk Doc Insert (10 Docs/Insert)",
         "randomRead":"Simple Random Doc Read",
         "randomUpdate":"Simple Random Doc Update"}
    
    for k in data:
        d = np.array(data[k])
        p95th = d[np.where(d < np.percentile(d,95))[0]]
        pylab.plot(p95th, label=k+"_95th percentile")
        pylab.plot([np.mean(p95th)]*len(p95th), label="mean")
        pylab.plot([np.median(p95th)]*len(p95th), label="median")
        pylab.xlabel("Test samples")
        pylab.ylabel("Response Time (s)")
        pylab.title(humanReadable[k])
        pylab.legend()
        pylab.ylim([0,np.max(p95th)*1.5])
        pylab.savefig(outdir+"/"+k+"_95th.png", dpi=200)
        pylab.clf()
        
        pylab.plot(d, label=k)
        pylab.plot([np.mean(d)]*len(d), label="mean")
        pylab.plot([np.median(d)]*len(d), label="median")
        pylab.xlabel("Test samples")
        pylab.ylabel("Response Time (s)")
        pylab.title(humanReadable[k])
        pylab.legend()
        pylab.ylim([0,np.max(d)*1.5])
        pylab.savefig(outdir+"/"+k+".png", dpi=200)
        pylab.clf()
    
    print "done generating plots.."

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given a TaskData.json, plot basic graphs for each top level item, expected format: {\"<taskname\":[<resp0>,<resp1>,<resp2>,..]}")
    parser.add_argument("--dataFile", dest="dataFile", default="./TaskData.json", help="Input Filename (Default: ./TaskData.json)")
    parser.add_argument("--outputDir", dest="outputDir", default="./plots", help="Output dir (Default: ./plots)")
    args = parser.parse_args()
    
    main(args.dataFile, args.outputDir)