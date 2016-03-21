#!/usr/bin/env bash


module purge
module unuse /software/modulefiles
module unuse /usr/share/Modules/modulefiles
module unuse /etc/modulefiles
shell=`/bin/basename $SHELL`
if [ -f /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/$shell ]
then
  . /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/$shell
else
  . /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/sh
fi