import pylab
import json
import numpy as np

data = json.load(open("TaskData.json"))
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
    pylab.show()

