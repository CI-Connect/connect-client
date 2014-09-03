#!/bin/bash

######################################################################################
# Functions definitions
######################################################################################

# Echo a line with the current date/time and the script who called

function f_echo () {

  _level=0
  _name="functions"


  # Find the first script not called "functions"

  while [[ "${_name}" == "functions" ]]; do
    _name=$(basename ${BASH_SOURCE[${_level}]} .sh)
    _level=$((_level+1))
    [[ ${_level} -gt 10 ]] && _name="*error*"
  done

  _date=$(date "+%d %b %H:%M:%S")
  _name=$(echo ${_name} | sed -e :a -e 's/^.\{1,15\}$/& /;ta')

  echo "${_date}| ${_name} | $@"

  return 0

}


# Set a ulimit value for a job with a default value

function f_ulimit () {

  _ulimitOPT=$1
  _ulimitDEF=$2
  _ulimitVAL=$3


  # If we have a preferred value, try to set it

  if [[ -n "${_ulimitVAL}" ]]; then
    ulimit -S ${_ulimitOPT} ${_ulimitVAL} 2>/dev/null
    _ulimitSTS=$?

    if [[ ${_ulimitSTS} -ne 0 ]]; then
      f_echo "Unable to set preferred ulimit ${_ulimitOPT} ${_ulimitVAL}"
    fi
  else
    _ulimitSTS=1
  fi

  # If we did not set a preferred value, try to set a default
  # If the default is "hard", use the Hard value

  if [[ ${_ulimitSTS} -ne 0 ]]; then

    [[ "${_ulimitDEF}" = "hard" ]] && _ulimitDEF=$(ulimit -H ${_ulimitOPT})

    ulimit -S ${_ulimitOPT} ${_ulimitDEF} 2>/dev/null
    _ulimitSTS=$?

    if [[ ${_ulimitSTS} -ne 0 ]]; then
      f_echo "Unable to set default ulimit ${_ulimitOPT} ${_ulimitDEF}"
      f_echo "Effective ulimit ${_ulimitOPT} $(ulimit -S ${_ulimitOPT})"
    fi
  fi

  return ${_ulimitSTS}

}


# Add a path to $PATH if it is missing

function f_addpath () {

  echo ${PATH} | /bin/egrep -q "(^|:)$1($|:)"

  if [[ $? -ne 0 ]]; then
    if [[ -z "${PATH}" ]]; then
      export PATH=$1
    else
      if [[ $2 == "^" ]]; then
        export PATH=$1:${PATH}
      else
        export PATH=${PATH}:$1
      fi
    fi
  fi

  return 0

}


# Add a path to $LD_LIBRARY_PATH if it is missing

function f_addldlibrarypath () {

  echo ${LD_LIBRARY_PATH} | /bin/egrep -q "(^|:)$1($|:)"

  if [[ $? -ne 0 ]]; then
    if [[ -z "${LD_LIBRARY_PATH}" ]]; then
      export LD_LIBRARY_PATH=$1
    else
      if [[ $2 == "^" ]]; then
        export LD_LIBRARY_PATH=$1:${LD_LIBRARY_PATH}
      else
        export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$1
      fi
    fi
  fi

  return 0

}