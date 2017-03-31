#!/bin/bash

# Name of the current testrun
# if unset it defaults to: sometest_`(date +"%Y%m%d_%H.%M.%S")`
testName=perf-benchmark_20150806_16.42.13
baselineName=Testy014_baseline_20150804
        
# server to host the result files
webHost=cds-perf01.rtp.raleigh.ibm.com
webHostPath=/var/www/html
webHostKey=/Users/tphan/.ssh/id_rsa_jenkins
user=ibmadmin
#------- Compress files to move over web host ------
echo "here is: " $testName
tar cfz ${testName}.tar.gz results/${testName}
tar cfz ${baselineName}.tar.gz results/${baselineName}

# regenerate the dashboard on web host machine
# Turn on no host checking
#----------- Push Report back to Repo Server -----------
echo "Publishing report.."
# pushing files to web root dir
scp -i $webHostKey ${testName}.tar.gz $user@$webHost:$webHostPath
scp -i $webHostKey ${baselineName}.tar.gz $user@$webHost:$webHostPath

# regenerate the dashboard on web host machine
# assuming the key is added into localhost .ssh 
# Or turn on no host checkingif don't have permission to add key 
scriptExec="cd $webHostPath;
tar xzf ${testName}.tar.gz;
#rm ${testName}.tar.gz;
tar xzf ${baselineName}.tar.gz;
#rm ${baselineName}.tar.gz;
python generatePages.py"
ssh -o StrictHostKeyChecking=no -l $user $webHost "$scriptExec"
