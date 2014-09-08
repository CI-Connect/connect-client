#!/bin/sh -x 

env 

# BLAHP does weird things with home directory
unset HOME
export HOME

# These must come after we fix HOME from BLAHP so ~ translates properly         
starting_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
eval campus_factory_dir=$_campusfactory_CAMPUSFACTORY_LOCATION

# Make certain the root of all job sandboxes exists and if not create it        
[[ ! -d ${_campusfactory_wntmp} ]] && mkdir -p ${_campusfactory_wntmp}

# Load up some useful functions                                                 
source ${starting_dir}/functions.sh

# Create this job's local sandbox                                               
local_dir=`mktemp -d -p ${_campusfactory_wntmp} rcc.XXXXXXXXXX`

# Copy the files we need into the job sandbox                                   
cp ${starting_dir}/passwdfile               ${local_dir}
cp ${starting_dir}/user_job_wrapper.sh      ${local_dir}
cp ${starting_dir}/exec_wrapper.sh          ${local_dir}
 
# Untar the executables into the sandbox                                        
tar --extract --gzip --directory=${local_dir} --file=${starting_dir}/glideinExec.tar.gz

# All late-binding configurations                                               
export CONDOR_CONFIG=${starting_dir}/glidein_condor_config
export _condor_LOCAL_DIR=${local_dir}
export _condor_START_DIR=${starting_dir}
export _condor_SBIN=${local_dir}/glideinExec
export _condor_LIB=${local_dir}/glideinExec
export _condor_USER_JOB_WRAPPER=${local_dir}/user_job_wrapper.sh
export LD_LIBRARY_PATH=$_condor_LIB

################################################################################
######                                                                          

# HTCondor Daemon Startup                                                       
# What are the current Maximum and Minimums specified for the slot life in minutes                                                                              
_MaxSlotLife=$((24*60))
_MinSlotLife=0

# The smallest slot life should be 30/15 minutes                                
[[ ${_MaxSlotLife} -lt 30 ]] && _MaxSlotLife=30
[[ ${_MinSlotLife} -lt 15 ]] && _MinSlotLife=15

# If the Mininum is greater than the Maximum, reset to only half of the Maximium
[[ ${_MinSlotLife} -ge ${_MaxSlotLife} ]] && _MinSlotLife=$((${_MaxSlotLife}/2))

# Compute the life of the daemons we will be starting in minutes                
# We terminate the Condor Daemons with 5 minutes remaining in the slot life 
# so that we can cleanup the job sandbox and avoid lengthly cleanups later.     
_DaemonTTL=$((${_MaxSlotLife} - ${_MinSlotLife} - 5))

# Save the daemon start time (now) along with the Maximum and Mininum of the slot life in seconds                                                               
export _condor_DaemonStartTime=$(date +%s)
export _condor_DaemonTTL=$((${_DaemonTTL}*60))
export _condor_DaemonRetireTime=$((${_condor_DaemonStartTime}+${_DaemonTTL}))
export _condor_MaxSlotLife=$((${_MaxSlotLife}*60))
export _condor_MimSlotLife=$((${_MinSlotLife}*60))

# -r   Retire the daemons when the slot life has only the minimum job start time remaining in minutes                                                           
# -f   Do not fork the daemons                                                  
# -dyn ??                                                                       
if [ "$_condor_LOCAL_DIR" = "." ]; then
  export _condor_LOCAL_DIR=$(pwd)
fi

#If we have an X509 user proxy, use it as the Condor daemon proxy.                   
if [ "$_condor_GSI_DAEMON_PROXY" = "" ] && [ -a "$X509_USER_PROXY" ]; then
  export _condor_GSI_DAEMON_PROXY="$X509_USER_PROXY"
fi

exec ${_condor_SBIN}/condor_master -dyn -f -r 1200 

######################################################################################   

rm -rf ${local_dir}
