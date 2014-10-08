#!/bin/sh

starting_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# BLAHP does weird things with home directory
unset HOME
export HOME

eval campus_factory_dir=$_campusfactory_CAMPUSFACTORY_LOCATION

# Make the temporary directory
if [ ! -d $_campusfactory_wntmp ]
then
  # See if we can make the designated directory
  mkdir -p $_campusfactory_wntmp
fi
local_dir=`mktemp -d -t -p $_campusfactory_wntmp`
cd $local_dir

# Copy the exec tar file
cp $starting_dir/glideinExec.tar.gz $local_dir
cp $starting_dir/passwdfile $local_dir

# Untar the executables
tar xzf $local_dir/glideinExec.tar.gz

# All late-binding configurations
export CONDOR_CONFIG=$starting_dir/glidein_condor_config
export _condor_LOCAL_DIR=$local_dir
export _condor_SBIN=$local_dir/glideinExec
export _condor_LIB=$local_dir/glideinExec

export LD_LIBRARY_PATH=$_condor_LIB

# Copy the user job wrapper
if [ -e $starting_dir/user_job_wrapper.sh ]
then
cp $starting_dir/user_job_wrapper.sh `pwd`
fi

if [ -e `pwd`/user_job_wrapper.sh ]
then
export _condor_USER_JOB_WRAPPER=`pwd`/user_job_wrapper.sh
fi

# Run on top of another glidein for condor-condor-condor action
unset _CONDOR_JOB_PIDS
unset _CONDOR_ANCESTOR_6635
unset _CONDOR_ANCESTOR_1130
unset _CONDOR_SCRATCH_DIR
unset _CONDOR_ANCESTOR_1092
unset _CONDOR_CHIRP_CONFIG
unset _CONDOR_ANCESTOR_1095
unset _CONDOR_WRAPPER_ERROR_FILE
unset _CONDOR_SLOT
unset _CONDOR_EXECUTE
unset _CONDOR_MACHINE_AD
unset _CONDOR_JOB_AD
unset _CONDOR_JOB_IWD

./glideinExec/glidein_startup -dyn -f -r 1200

rm -rf $local_dir
