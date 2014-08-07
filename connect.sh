#!/bin/bash
# borrows heavily from bosco_quickstart, first version 5/2/2013, by Marco Mambelli

# Change to have a different log file
LOG_FILE=~/./bosco/connect_setup.log
# To have no log file use:
# LOG_FILE=/dev/null

fix_port () {
  # Checks if the port is available
  # If the port is already used it sweeps until a port is available
  which netstat &> /dev/null
  if [ $? -ne 0 ]; then
    echo "No netstat available, unable to verify if port $1 is free" >> $LOG_FILE
    return 1
  fi
  let start_port=$1
  let tmp_max=$start_port+2000
  let tmp_port=$start_port
  while [ $tmp_port -le $tmp_max ]; do
    netstat -tulpn 2> /dev/null | grep $tmp_port > /dev/null 2>&1
    [ $? -eq 1 ]  && break
    let tmp_port=$tmp_port+1
  done
  if [ $tmp_port -eq $start_port ]; then
    # Initil port is available
    return 0
  fi
  if [ $tmp_port -le $tmp_max ]; then
    # Found a free port in the range
    factory_config=$HOME/bosco/local.bosco/config/condor_config.factory
    echo "Port $start_port is busy. Replacing port $start_port with $tmp_port. Before:" >> $LOG_FILE
    grep $start_port $factory_config >> $LOG_FILE
    sed "s;$start_port;$tmp_port;" < $factory_config > ${factory_config}.new
    mv ${factory_config}.new ${factory_config}
    echo "After replacement:" >> $LOG_FILE
    grep $tmp_port $factory_config >> $LOG_FILE
    return 0
  fi
  echo "No free port in range $start_port to $tmp_port" >> $LOG_FILE
  return 1
}

# Create condor_config file

CONDOR_CONFIG=~/.bosco/condor_config
touch $CONDOR_CONFIG

CONDOR_CONFIG <<EOF
##  Where have you installed the bin, sbin and lib condor directories?
RELEASE_DIR = /usr/local/condor

##  Where is the machine-specific local config file for each host?
#LOCAL_CONFIG_FILE = /software/bosco/local.bosco/condor_config.local
LOCAL_CONFIG_FILE = /home/antonyu/bosco_copy/local.bosco/condor_config.local
LOCAL_CONFIG_DIR = $(LOCAL_DIR)/config

##  Use a host-based security policy. By default CONDOR_HOST and the local machine will be allowed
use SECURITY : HOST_BASED

EOF

# Check if Bosco is already started (better way?)
echo "Connect Setup is starting."
echo "More information can be found in $LOG_FILE"
echo
bosco_stop &> /dev/null
if [ $? -eq 127 ]; then
    # check if port 11000 (BOSCO default) is available
    fix_port 11000

    # Start Bosco
    echo "************** Starting Bosco: ***********"
    bosco_start
else
    echo "Bosco already started." 
    # check if UChicago Connect cluster added?
fi

# Connect UChicago Connect cluster
REMOTE_HOST="login.ci-connect.uchicago.edu"
REMOTE_USER=""
REMOTE_TYPE="condor"
echo "************** Connecting UChicago Connect cluster to BOSCO: ***********"
echo "At any time hit [CTRL+C] to interrupt."
echo 

q_tmp=""
read -p "Type your username on $REMOTE_HOST (default $USER) and press [ENTER]: " q_tmp
if [ "x$q_tmp" = "x" ]; then 
  REMOTE_USER=$USER
else
  REMOTE_USER=$q_tmp
fi

echo "Connecting $REMOTE_HOST, user: $REMOTE_USER, queue manager: $REMOTE_TYPE"
bosco_cluster --add $REMOTE_USER@$REMOTE_HOST $REMOTE_TYPE 

if [ $? -ne 0 ]; then
  echo "Failed to connect the cluster $REMOTE_HOST. Please check your data and retry."
  exit 2
fi

echo "$REMOTE_HOST connected"

echo "************** Testing the cluster (resource): ***********"
#echo "This may take up to 2 minutes... please wait."
show_progress "This may take up to 2 minutes... please wait." bosco_cluster --test $REMOTE_USER@$REMOTE_HOST 
# MMDB move this underneath 
echo "BOSCO on $REMOTE_HOST Tested"
if [ $? -ne 0 ]; then
  echo "Failed to test the cluster $REMOTE_HOST. Please check your data and retry."
  exit 3
fi

echo "************** Congratulations, Bosco is now setup to work with $REMOTE_HOST! ***********"
cat << EOF
You are ready to submit jobs with the "condor_submit" command.
Remember to setup the environment all the time you want to use Bosco:
module load bosco

Here is a quickstart guide about BOSCO:
https://twiki.grid.iu.edu/bin/view/CampusGrids/BoscoQuickStart

To remove Bosco you can run:
module load bosco; bosco_uninstall --all

Here is a submit file example (supposing you want to run "myjob.sh"):
universe = grid
grid_resource = batch condor $REMOTE_USER@$REMOTE_HOST
Executable = myjob.sh
arguments = 
output = myjob.output.txt
error = myjob.error.txt
log = myjob.log
transfer_output_files = 
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
queue 1
EOF
