#!/bin/sh
#
# @help @ user@hostname sched-type
#

NAME="UChicago CI Connect"
LOCAL_DIR=$HOME/.bosco

# Change to have a different log file
LOG_FILE=$LOCAL_DIR/connect_addsite.log
# To have no log file use:
# LOG_FILE=/dev/null

# Check if Bosco has been started
started=$(ps ux | grep condor_master | wc -l)
if [ $started -eq 1 ]; then
    echo "$NAME not started. Please run 'connect setup' first and try again."
fi

REMOTE_HOST="" 
REMOTE_USER=""
REMOTE_TYPE="condor"

usage ()  {
	echo >&2 "usage: connect addsite user@hostname sched-type"
	echo >&2 "       'sched-type' is a word denoting the type of scheduler"
	echo >&2 "       running at hostname.  It should be 'slurm', 'pbs',"
	echo >&2 "       'condor', 'lsf', or 'sge'."
}

if [ $# -ne 2 ]; then
	usage
	exit 2
fi

target=$1
type=$(echo $2 | tr '[A-Z]' '[a-z]')

case $type in
	slurm)	type=pbs;;
	pbs)	: ;;
	sge)	: ;;
	condor)	: ;;
	lsf)	: ;;
	*)		usage; exit 10;;
esac

echo "Connecting to a $type scheduler at $target..."
bosco_cluster --add $target $type 2>> $LOG_FILE

if [ $? -ne 0 ]; then
	echo "Failed to connect to $target. Please check your information and retry."
	exit 20
fi

echo "$target is connected."


echo "**** Testing the cluster (resource): ****"
echo "This may take up to 2 minutes... please wait."
test=$(bosco_cluster --test $target 2>> $LOG_FILE)
echo "$NAME on $target Tested"
if [ $? -ne 0 ]; then
  echo "Failed to test the cluster $target. Please check your information and retry."
  exit 30
fi

echo **** Congratulations, $NAME is now setup to work with $REMOTE_HOST! ****"
cat >/dev/tty <<EOF
You are ready to submit jobs with the "condor_submit" command.
Remember to setup the environment each time you want to use $NAME:
module load connect
EOF
