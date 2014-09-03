#!/bin/sh 

# BLAHP does weird things with home directory

# Remove $HOME so that ~ translates to our true HOME
# But leave $HOME blank otherwise jobs will try to use $HOME as their Working Directory
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

# We want to lock our working area to prevent removal
export _condor_LOCKFILE=${local_dir}.lock

# Create the lock file
${starting_dir}/lockfile -0 -r 0 ${_condor_LOCKFILE}

# If we could not create the lock file, exit with an error
lockstatus=$?

if [[ ${lockstatus} -ne 0 ]]; then
    f_echo "Unable to create the lockfile ${_condor_LOCKFILE}"
    exit ${lockstatus}
fi

# Copy the files we need into the job sandbox
cp ${starting_dir}/passwdfile               ${local_dir}
cp ${starting_dir}/lockfile                 ${local_dir}
cp ${starting_dir}/SlotIsHealthy.sh         ${local_dir}
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

######################################################################################

# Setup $LD_LIBRARY_PATH
# We put the system libraries before the GlideinExec libraries (older) to avoid any contention

# Add in the system libraries
f_addldlibrarypath "/usr/lib64"
f_addldlibrarypath "/lib64"
f_addldlibrarypath "/usr/lib"
f_addldlibrarypath "/lib"

# Add in the libraries from /usr/local
f_addldlibrarypath "/usr/local/lib64"
f_addldlibrarypath "/usr/local/lib"

# Append the glideinExec libraries into the search path
f_addldlibrarypath "${_condor_LIB}"

######################################################################################

# Setup the ulimits for the glidein and user job
# These will become the hard caps for the user job

f_echo
f_echo "Maximizing unlimits for Glidein"

f_ulimit -t  hard  $((<%= bosco_maxslotlife %>*60))
f_ulimit -d  hard  unlimited
f_ulimit -f  hard  unlimited
f_ulimit -l  hard  unlimited
f_ulimit -n  hard  unlimited
f_ulimit -s  hard  unlimited
f_ulimit -m  hard  unlimited
f_ulimit -u  hard  unlimited
f_ulimit -v  hard  unlimited
f_ulimit -x  hard  unlimited

f_echo
f_echo "Executing command: ulimit -S -a"
f_echo

ulimit -S -a

f_echo
f_echo "Executing command: ulimit -H -a"
f_echo

ulimit -H -a

f_echo

######################################################################################
# This will cleanup any directories left behind in the RCC area from previous jobs
# If the local job scheduler kill the jobs (or the node crashes or), the job sandbox remains

function f_RCCcleaner () {

  # This is the directory we are to remove
  _lockdir=$1

  # Remove any locks which are older than our Maximum Slot Life
  _locktimeout=$((<%= bosco_maxslotlife %>*60))

  # Make certain that is a directory

  if [[ ! -d ${_lockdir} ]]; then
    f_echo "Illegal attempt to cleanup a non-RCC area - ${_lockdir}"
    return 255
  fi

  # Attempt to create a lockfile on the directory with a timeout
  ${_condor_START_DIR}/lockfile -0 -r 0 -s 0 -l ${_locktimeout} ${_lockdir}.lock 2> /dev/null

  # If we got a lock, we can safely remove the file and then the lock
  _lockstatus=$?

  if [[ ${_lockstatus} -eq 0 ]]; then
    rm -rf ${_lockdir}
    rm -f  ${_lockdir}.lock
  fi

  return ${_lockstatus}

}

# Export this function so we can find it
export -f f_RCCcleaner

# Lock the cleanup to one job per node with a 1 hour timeout on the lock
${_condor_START_DIR}/lockfile -0 -r 0 -s 0 -l $((1*60*60)) ${_campusfactory_wntmp}/rcc.lock

# Proceed only if we got the lock
if [[ $? -eq 0 ]]; then
  # Cleanup the RCC factory area of any directories older than 1 hour that are not active
  find  ${_campusfactory_wntmp}/rcc.* -ignore_readdir_race -maxdepth 0 -xdev -amin +60 -type d -exec bash -c 'f_RCCcleaner "{}"' \;
  rm -f ${_campusfactory_wntmp}/rcc.lock
fi

# Remove this function
unset -f f_RCCcleaner

######################################################################################

# If we are using PortableCVMFS to access the repositories, we must mount them
# A mount point of "/cvmfs" assume we are getting the whole node for this glidein
# Otherwise other users could have issues accessing the repositories

if [[ "<%= bosco_cvmfs %>" == "portable" ]]; then
  ${_condor_LOCAL_DIR}/connect/PortableCVMFS/bin/WrapperMount.sh "<%= bosco_cvmfsmount %>" "<%= bosco_cvmfsscratch %>" "<%= bosco_cvmfsquota %>" "<%= bosco_cvmfsproxy %>"
fi

######################################################################################

# HTCondor Daemon Startup

# What are the current Maximum and Minimums specified for the slot life in minutes
_MaxSlotLife=<%= bosco_maxslotlife %>
_MinSlotLife=<%= bosco_minslotlife %>

# If no values were given, setup a default of 1 day
[[ -z "${_MaxSlotLife}"  ]] && _MaxSlotLife=$((24*60))
[[ -z "${_MinSlotLife}"  ]] && _MinSlotLife=0

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

${_condor_LOCAL_DIR}/glideinExec/glidein_startup -dyn -f -r ${_DaemonTTL}

######################################################################################

# If we are using PortableCVMFS, umount on the way out but do not remove the cache
if [[ "<%= bosco_cvmfs %>" == "portable" ]]; then
  ${_condor_LOCAL_DIR}/connect/PortableCVMFS/bin/WrapperUmount.sh "<%= bosco_cvmfsmount %>" "<%= bosco_cvmfsscratch %>"
fi

######################################################################################

# Remove this working directory
rm -rf ${local_dir}

######################################################################################

# Remove the lock on this working directory
rm -f ${_condor_LOCKFILE}

######################################################################################