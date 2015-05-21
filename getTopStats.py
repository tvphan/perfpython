import subprocess
import datetime as dt

cpuStats = {}
p = subprocess.Popen(["top", "-b", "-n 2"], stdout=subprocess.PIPE)
(output, err) = p.communicate()
 
# wait for command to finish..
p_status = p.wait()

if p_status == 0:
    for l in output.split("\n"):
        if "Cpu(s)" in l:
            bits = l.split(":")[1].split(",")
            for b in bits:
                cpuStats[b[-3:]] = float(b[:-3])

print {"timestamp": str(dt.datetime.now()), "cpuStats":cpuStats }