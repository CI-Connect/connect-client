#!/bin/bash
if [ $# -ne 1 ]; then
  JOB_HISTORY_CMD=$(condor_history `whoami` | head -n2 | tail -n1 | cut -d'.' -f1)
else
  JOB_HISTORY_CMD=$(condor_history $1 | head -n2 | tail -n1 | cut -d'.' -f1)
fi

condor_history -format '%s\n' LastRemoteHost $JOB_HISTORY_CMD \
| awk -F@ '{print $NF}' \
| rev \
| cut -d'.' -f1,2 \
| rev \
| sed -e 's/qgp[0-9][0-9]\|lqcd[0-9][0-9]\|neutrino-[0-9][0-9]\|neuron-[0-9][0-9]\|neutron-[0-9][0-9]\|nano[0-9][0-9]/duke.edu/' \
      -e 's/compute-[0-9][0-9]-[0-9][0-9]\.local[0-9]\|compute-[0-9]-[0-9][0-9].nysu[0-9]/uconn.edu/' \
      -e 's/nodo[0-9][0-9]/cinvestav.mx/' \
      -e 's/compute-[0-9]-[0-9].local/vt.edu/' \
      -e 's/node[0-9][0-9][0-9].local/unesp.br/' \
      -e 's/compute-[0-9]-[0-9][0-9].nys1\|compute-[0-9]-[0-9].nys1\|compute-[0-9]-[0-9][0-9].local/atlas-swt2.org/' \
      -e 's/golub[0-9][0-9][0-9]\|taub[0-9][0-9][0-9]/mwt2.org/' \
      -e 's/iu.edu/mwt2.org/' \
      -e 's/midway[0-9][0-9][0-9]\|midway-[a-z][0-9][0-9]-[0-9][0-9]/rcc.uchicago.edu/' \
| distribution --color --char=pb
