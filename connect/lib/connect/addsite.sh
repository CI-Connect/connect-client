#!/bin/sh

LOCAL_DIR=$HOME/.bosco

# Change to have a different log file
LOG_FILE=$LOCAL_DIR/connect_addsite.log
# To have no log file use:
# LOG_FILE=/dev/null

# Check if Bosco has been started
started=$(ps ux | grep condor_master | wc -l)
if [ $started -eq 1 ]; then
    echo "Bosco not started. Please run 'connect setup' first and try again."
fi

REMOTE_HOST="" 
REMOTE_USER=""
REMOTE_TYPE="condor"

# Connect cluster

    q_tmp=""
    read -p "Type the site you would like to submit jobs to and press [ENTER]: " q_tmp </dev/tty
    REMOTE_HOST=$q_tmp

    q_tmp=""
    read -p "Type your username on $REMOTE_HOST (default $USER) and press [ENTER]: " q_tmp </dev/tty
    if [ "x$q_tmp" = "x" ]; then 
	REMOTE_USER=$USER
    else
	REMOTE_USER=$q_tmp
    fi

    echo "Connecting $REMOTE_HOST, user: $REMOTE_USER, queue manager: $REMOTE_TYPE"
    bosco_cluster --add $REMOTE_USER@$REMOTE_HOST $REMOTE_TYPE 2>> $LOG_FILE

    if [ $? -ne 0 ]; then
	echo "Failed to connect the cluster $REMOTE_HOST. Please check your data and retry."
	exit 2
    fi

    echo "$REMOTE_HOST connected"
fi

echo "************** Testing the cluster (resource): ***********"
echo "This may take up to 2 minutes... please wait."
test=$(bosco_cluster --test $REMOTE_USER@$REMOTE_HOST 2>> $LOG_FILE)
echo "BOSCO on $REMOTE_HOST Tested"
if [ $? -ne 0 ]; then
  echo "Failed to test the cluster $REMOTE_HOST. Please check your data and retry."
  exit 3
fi

if [ "x$REMOTE_USER" = "x" ]; then
    REMOTE_USER="username"
fi

echo "************** Congratulations, Bosco is now setup to work with $REMOTE_HOST! ***********"
cat >/dev/tty <<EOF
You are ready to submit jobs with the "condor_submit" command.
Remember to setup the environment all the time you want to use Bosco:
module load connect

Here is a quickstart guide about BOSCO:
https://twiki.grid.iu.edu/bin/view/CampusGrids/BoscoQuickStart

To remove Bosco you can run:
module load connect; bosco_uninstall --all

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
