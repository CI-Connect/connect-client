#!/bin/bash

RETRY=3 
SLEEP=3
LOGDIR=~/.bosco/log/connect.log


echo "# Reset $(date +%s) #" >> $LOGDIR


# condor_rm the glideins
function remove_glidein_jobs {
  if [ $(condor_q | grep glidein 2>&1 >> $LOGDIR ; echo $?) -eq 0 ]; then
    echo -n "Cleaning up glidein_wrapper jobs..."
    condor_rm $(condor_q | grep glidein | awk '{print $1}' | xargs) 2>&1 >> $LOGDIR
    condor_rm -forcex $(condor_q | grep glidein | awk '{print $1}' | xargs) 2>&1 >> $LOGDIR
    echo "OK"
  fi
}

function clean_existing_glideins {
  if [ $(bosco_cluster -l | grep midway 2>&1 >> $LOGDIR; echo $?) -eq 0 ]; then
    echo -n "Cleaning up running glideins on Midway..."
    qdel $(qstat | grep `whoami` | grep bl_ | awk '{print $1}') 2>&1 >> $LOGDIR
    echo "OK"
  fi
  # We need functionality to SSH to remote and clean up those as well
}

function stop_condor {
echo -n "Stopping Condor..." 
bosco_stop 2>&1 >> $LOGDIR
sleep $SLEEP
echo "OK"
}
function start_condor {
echo -n "Starting Condor..." 
bosco_start 2>&1 >> $LOGDIR
sleep $SLEEP
echo "OK"
}

# Check if Condor is running
for i in {1..$RETRY}; do 
  if [ $(condor_q 2>&1 > $LOGDIR 2>&1 >> $LOGDIR ; echo $?) -ne 0 ]; then
    start_condor
    sleep $SLEEP 
  else 
    break
  fi
done

remove_glidein_jobs
clean_existing_glideins
stop_condor
start_condor

echo "# Done #" >> $LOGDIR
