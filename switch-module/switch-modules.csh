#!/bin/tcsh

switch ($2)
case oasis:
  echo ". /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/$1"
  breaksw
case local:
  echo ". /srv/adm/modules/init/$1"
  breaksw
endsw
