#!/bin/sh
#
# @usage [seconds [user]]
#

if [ $# -gt 0 ]; then
	sec=$1; shift
	opts="-n$sec"
else
	opts="-n5"
fi

if [ $# -gt 0 ]; then
	sec=$1; shift
	args="$@"
else
	args="$(whoami)"
fi

/usr/bin/watch $opts condor_q $args
