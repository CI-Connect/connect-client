#!/bin/sh

if [ "$#" -ne 1 ]; then
	echo "Usage: condor_job_distribution job-id" >&2 
	exit 1
fi 

condor_history -format '%s\n' LastRemoteHost $1 | cut -d@ -f2 | /usr/local/bin/distribution --height=100
