#!/bin/sh
# based on bosco_quickstart, first version 5/2/2013, by Marco Mambelli

#PROD="Bosco"
PROD="Connect Client"
LOCAL_DIR=$HOME/.bosco

# Infer the bosco directory from our own path.
BASEDIR=$(dirname ${ARGV0DIR-/})
BOSCO_DIR=$BASEDIR/bosco # change to /software/bosco later

REMOTE_HOST="login.ci-connect.uchicago.edu"
REMOTE_USER=$1
REMOTE_TYPE="condor"

CANONICAL_HOST="midway-login1"
CANONICAL_HOST_LONG="midway-login1.rcc.uchicago.edu"

# Change to have a different log file
LOG_FILE=$LOCAL_DIR/connect_setup.log
# To have no log file use:
# LOG_FILE=/dev/null

CONFIG_FILE=$LOCAL_DIR/condor_config
LOCAL_CONFIG=$LOCAL_DIR/condor_config.local
factory_config=$LOCAL_DIR/config/condor_config.factory

banner () {
	echo "******** $@ ********"
}

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
      # Initial port is available
      echo "Port $tmp_port available." >> $LOG_FILE
  elif [ $tmp_port -le $tmp_max ]; then
	  # Found a free port in the range	 
          echo "Found available port $tmp_port." >> $LOG_FILE
  else 
      echo "No free port in range $start_port to $tmp_port" >> $LOG_FILE
      return 1
  fi
  old_port=$(grep SHARED_PORT_ARGS $factory_config | cut -d ' ' -f 4)
  if [ $old_port -eq $tmp_port ]; then
      echo "Still using $tmp_port." >> $LOG_FILE
  else
      echo "Port $old_port is busy. Replacing $old_port with $tmp_port. Before:" >> $LOG_FILE
      grep $old_port $factory_config >> $LOG_FILE
      sed "s;$old_port;$tmp_port;" < $factory_config > ${factory_config}.new
      mv ${factory_config}.new ${factory_config}
      echo "After replacement:" >> $LOG_FILE
      grep $tmp_port $factory_config >> $LOG_FILE
      return 0
  fi
  return 1
}

# User must log in on $CANONICAL_HOST node.  
HOST_NAME=$(hostname)
if [ "$HOST_NAME" != "$CANONICAL_HOST" ];then
	user=$(whoami)
	fmt -w75 <<EOF
You are logged in on $HOST_NAME. Please log in on $CANONICAL_HOST_LONG to access the Connect module.
To do this, type 'logout' and then 'ssh $user@$CANONICAL_HOST_LONG' to log in to $CANONICAL_HOST.
EOF
    exit
fi

if [ "$#" -ne 1 ]; then
    echo "Usage: connect setup <RCC Connect username>"
    echo "       connect setup -uninstall"
    exit
fi

if [ "$(echo $1 | tr -d -)" = "uninstall" ]; then
	echo "Uninstalling Connect Client configuration."
	(
		bosco_stop
		killall condor_master
		rm -rf $HOME/.bosco
		cd $HOME/.ssh
		for file in bosco*; do
			mv "$file" "$file.old"
		done
	) 2>/dev/null
	exit $?
fi

echo "Connect Setup is starting."
echo "More information can be found in $LOG_FILE"
echo

# Check to see if local Bosco directory and all subdirectories exist.
# If not, create them.

[ -d $LOCAL_DIR ] || mkdir $LOCAL_DIR && echo "Local $PROD files can be found in $LOCAL_DIR" >> $LOG_FILE
[ -d $LOCAL_DIR/log ] || mkdir $LOCAL_DIR/log && touch $LOCAL_DIR/log/MasterLog
[ -d $LOCAL_DIR/spool ] || mkdir $LOCAL_DIR/spool
[ -d $LOCAL_DIR/execute ] || mkdir $LOCAL_DIR/execute
[ -d $LOCAL_DIR/config ] || mkdir $LOCAL_DIR/config

# Check if config files exist.
exists=1
[ -f $CONFIG_FILE ] || exists=0
[ $exists -eq 0 ] && cat > $CONFIG_FILE <<EOF
######################################################################
##
##  condor_config
##
##  This is the global configuration file for condor. This is where
##  you define where the local config file is. Any settings
##  made here may potentially be overridden in the local configuration
##  file.  KEEP THAT IN MIND!  To double-check that a variable is
##  getting set from the configuration file that you expect, use
##  condor_config_val -v <variable name>
##
##  condor_config.annotated is a more detailed sample config file
##
##  Unless otherwise specified, settings that are commented out show
##  the defaults that are used if you do not define a value.  Settings
##  that are defined here MUST BE DEFINED since they have no default
##  value.
##
######################################################################

##  Where have you installed the bin, sbin and lib condor directories?   
RELEASE_DIR = /usr/local/condor

##  Where is the machine-specific local config file for each host?
LOCAL_CONFIG_FILE = $LOCAL_DIR/condor_config.local

EOF

[ $exists -eq 0 ] && echo '##  The normal way to do configuration with RPMs is to read all of the
##  files in a given directory that do not match a regex as configuration files.
##  Config files are read in lexicographic order.
LOCAL_CONFIG_DIR = $(LOCAL_DIR)/config
#LOCAL_CONFIG_DIR_EXCLUDE_REGEXP = ^((\..*)|(.*~)|(#.*)|(.*\.rpmsave)|(.*\.rpmnew))$

##  Use a host-based security policy. By default CONDOR_HOST and the local machine will be allowed
use SECURITY : HOST_BASED
##  To expand your condor pool beyond a single host, set ALLOW_WRITE to match all of the hosts
#ALLOW_WRITE = *.cs.wisc.edu' >> $CONFIG_FILE

HOST=$CANONICAL_HOST_LONG
USER=$(whoami)
CONDOR_ID=$(id -u)

[ -f $LOCAL_CONFIG ] || cat > $LOCAL_CONFIG <<EOF

##  Where have you installed the bin, sbin and lib condor directories?   

RELEASE_DIR = $BOSCO_DIR

##  Where is the local condor directory for each host?  This is where the local config file(s), logs and
##  spool/execute directories are located. this is the default for Linux and Unix systems.
##  this is the default on Windows sytems

LOCAL_DIR = $LOCAL_DIR

COLLECTOR_NAME = Personal Condor at $HOST

NETWORK_INTERFACE = 128.135.112.71

MY_FULL_HOSTNAME = $HOST

FILESYSTEM_DOMAIN = $HOST

UID_DOMAIN = $HOST

COLLECTOR_ARGS = -sock collector

LOCK = /tmp/condor-lock.$USER

IS_BOSCO = True

CONDOR_ADMIN =  

MAIL = /bin/mailx

GANGLIAD_METRICS_CONFIG_DIR = $BOSCO_DIR/etc/condor/ganglia.d

DAEMON_LIST = COLLECTOR, MASTER, NEGOTIATOR, SCHEDD, STARTD

PREEN_ARGS = -r

CONDOR_HOST = $HOST

CONDOR_IDS = $CONDOR_ID.$CONDOR_ID

CREATE_CORE_FILES = False

GRIDMANAGER_MAX_SUBMITTED_JOBS_PER_RESOURCE=10

EOF

[ -f $factory_config ] || echo '#
# Things you have to edit
#

##  What machine is your central manager?
NETWORK_HOSTNAME = $CANONICAL_HOST_LONG
CONDOR_HOST = $(NETWORK_HOSTNAME)
COLLECTOR_HOST = $(NETWORK_HOSTNAME):11000?sock=collector

# What hosts can run jobs to this cluster.
FLOCK_FROM = 

# Jobs submitted here can run at.
FLOCK_TO = 

##############################################
# Things that are safe to leave
#

CAMPUSFACTORY = $(SBIN)/runfactory
CAMPUSFACTORY_ARGS = -c $(LIBEXEC)/campus_factory/etc/campus_factory.conf
CAMPUSFACTORY_ENVIRONMENT = "PYTHONPATH=$(LIBEXEC)/campus_factory/python-lib CAMPUSFACTORY_DIR=$(LIBEXEC)/campus_factory _campusfactory_GLIDEIN_DIRECTORY=$(LIBEXEC)/campus_factory/share/glidein_jobs"

# Enabled Shared Port
USE_SHARED_PORT = True
SHARED_PORT_ARGS = -p 11000

# What daemons should I run?
DAEMON_LIST = COLLECTOR, SCHEDD, NEGOTIATOR, MASTER, SHARED_PORT, CAMPUSFACTORY

# Remove glidein jobs that get put on hold for over 24 hours.
SYSTEM_PERIODIC_REMOVE = (GlideinJob == TRUE && JobStatus == 5 && time() - EnteredCurrentStatus > 3600*24*1)

#
# Security definitions
#
SEC_ENABLE_MATCH_PASSWORD_AUTHENTICATION = TRUE

SEC_DEFAULT_ENCRYPTION = OPTIONAL
SEC_DEFAULT_INTEGRITY = REQUIRED
# To allow status read
SEC_READ_INTEGRITY = OPTIONAL

ALLOW_ADMINISTRATOR = $(MY_FULL_HOSTNAME) $(IP_ADDRESS) $(FULL_HOSTNAME)

ALLOW_NEGOTIATOR = $(ALLOW_NEGOTIATOR) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_NEGOTIATOR_SCHEDD = $(ALLOW_NEGOTIATOR_SCHEDD) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_OWNER = $(ALLOW_OWNER) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_READ_COLLECTOR = $(ALLOW_READ_COLLECTOR) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_READ_STARTD = $(ALLOW_READ_STARTD) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_WRITE = $(ALLOW_WRITE) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_WRITE_COLLECTOR = $(ALLOW_WRITE_COLLECTOR) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)
ALLOW_WRITE_STARTD = $(ALLOW_WRITE_STARTD) $(MY_FULL_HOSTNAME) $(FULL_HOSTNAME)

SEC_PASSWORD_FILE = $(LOCAL_DIR)/passwdfile

# Daemons have their own passwdfile, always owned by the daemon user
COLLECTOR.SEC_PASSWORD_FILE = $(LOCAL_DIR)/passwdfile.daemon
NEGOTIATOR.SEC_PASSWORD_FILE = $(LOCAL_DIR)/passwdfile.daemon
GRIDMANAGER.SEC_PASSWORD_FILE = $(LOCAL_DIR)/passwdfile.daemon

SEC_ADVERTISE_STARTD_AUTHENTICATION = REQUIRED
SEC_ADVERTISE_STARTD_INTEGRITY = REQUIRED
SEC_ADVERTISE_STARTD_AUTHENTICATION_METHODS = PASSWORD
SEC_CLIENT_AUTHENTICATION_METHODS = FS, PASSWORD

ALLOW_ADVERTISE_STARTD = condor_pool@*/*
ALLOW_DAEMON = $(ALLOW_DAEMON) condor_pool@*/* $(MY_FULL_HOSTNAME) $(IP_ADDRESS) $(FULL_HOSTNAME)

SEC_DAEMON_AUTHENTICATION = REQUIRED
SEC_DAEMON_INTEGRITY = REQUIRED
SEC_DAEMON_AUTHENTICATION_METHODS = FS,PASSWORD
SEC_WRITE_AUTHENTICATION_METHODS = FS,PASSWORD

' > $factory_config

# Stop Bosco if already started (commented out as may be necessary in the future)
# bosco_stop --force > /dev/null

# Start Bosco if not started
started=$(ps ux | grep condor_master | wc -l)
if [ $started -eq 1 ]; then
    # set and check user-specific port 
    ID=`expr $(id -u) % 64511`
    PORT=`expr $ID + 1024`
    fix_port $PORT

    # Start Bosco
    banner "Starting $PROD:"
    bosco_start 2>> $LOG_FILE 1>/dev/tty
else
    echo "$PROD already started."
fi

# function for adding Midway cluster 
add_midway () {

    # Correct permissions on ~/.ssh to allow key-based authentication
    chmod -R g-w ~/.ssh

    # Check if the cluster is already added
    midway_set=$(bosco_cluster -l | grep $CANONICAL_HOST | wc -w)
    if [ $midway_set -eq 1 ]; then
	echo "Midway cluster already added."
    else
	# Connect Midway cluster
	banner "Connecting local Midway cluster to BOSCO:"
	echo "At any time hit [CTRL+C] to interrupt."
	echo
	bosco_cluster --add $USER@$HOST PBS 2>> $LOG_FILE
    
	if [ $? -ne 0 ]; then
            echo "Failed to connect the Midway cluster. Please check $LOG_FILE for more information."
	    exit
	fi
	
	echo
	echo "Midway cluster connected"

	# Test the cluster using bosco_cluster --test
	if false; then
		echo 
		banner "Testing the cluster (resource):"
		echo "This may take up to 2 minutes... please wait."
		test=$(bosco_cluster --test $USER@$HOST 2>> $LOG_FILE)
		echo "BOSCO on $CANONICAL_HOST_LONG tested"
		if [ $? -ne 0 ]; then
	    	echo "Failed to test the cluster $CANONICAL_HOST_LONG. Please check your data and retry."
	    	exit 3
		fi
	fi

	echo
	echo "Congratulations, $PROD is now setup to work with $CANONICAL_HOST_LONG!"
	
    fi
}

# function for adding RCC Connect cluster 
add_connect () {
    banner "Connecting RCC Connect cluster to BOSCO:"
    echo "At any time hit [CTRL+C] to interrupt."
    echo 
    
    echo "Connecting $REMOTE_HOST, user: $REMOTE_USER, queue manager: $REMOTE_TYPE"
    bosco_cluster --add $REMOTE_USER@$REMOTE_HOST $REMOTE_TYPE 2>> $LOG_FILE

    if [ $? -ne 0 ]; then
	echo "Failed to connect the cluster $REMOTE_HOST. Please check your data and retry."
	exit 2
    fi
    
    echo
    echo "$REMOTE_HOST connected"
    
    # Test the cluster with bosco_cluster --test
    echo 
    banner "Testing the cluster (resource):"
    echo "This may take up to 2 minutes... please wait."
    test=$(bosco_cluster --test $REMOTE_USER@$REMOTE_HOST 2>> $LOG_FILE)
    echo "BOSCO on $REMOTE_HOST tested"
    if [ $? -ne 0 ]; then
	echo "Failed to test the cluster $REMOTE_HOST. Please check your data and retry."
	exit 3
    fi

    echo
    echo "Congratulations, $PROD is now setup to work with $REMOTE_HOST!" 
    echo
}

# Check if the RCC Connect cluster is already added. 
# If not, add the cluster, then check the Midway cluster. 

RCC_set=$(bosco_cluster -l | grep $REMOTE_HOST | wc -w)
[ $RCC_set -eq 1 ] && echo "RCC Connect cluster already added." # && add_midway
[ $RCC_set -eq 0 ] && add_connect # && add_midway

cat >/dev/tty <<EOF
You are ready to submit jobs with the "condor_submit" command.
Remember to set up the environment each time you want to use $PROD:
module load connect

Here is a quickstart guide about BOSCO:
https://twiki.grid.iu.edu/bin/view/CampusGrids/BoscoQuickStart

For more help, here is the RCC Connect Handbook:
https://ci-connect.atlassian.net/wiki/display/UCHI/Home

Here is a submit file example (supposing you want to run "myjob.sh"):
universe = vanilla
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
