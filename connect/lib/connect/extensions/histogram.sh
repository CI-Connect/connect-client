#!/bin/bash
USER=$1
condor_q -run "$@" | grep -v "???" | grep -v ID| grep -v Submitter | rev | cut -d'.' -f1,2 | rev | grep -v "^[ ]*$\|^#" | distribution --color --char=pb 
