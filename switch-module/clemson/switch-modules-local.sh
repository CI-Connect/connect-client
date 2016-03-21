#!/usr/bin/env bash

module unuse /cvmfs/oasis.opensciencegrid.org/osg/modules/modulefiles/
module purge
shell=`/bin/basename $SHELL`
if [ -f /usr/share/Modules/init/$shell ]
then
  . /usr/share/Modules/init/$shell
else
  . /usr/share/Modules/init/sh
fi