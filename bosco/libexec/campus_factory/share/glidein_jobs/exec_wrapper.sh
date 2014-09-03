

#!/bin/bash

#################
# If a node is to run Atlas Pilots, they must use the Parrot Wrapper in Native mode

# These are needed to run an Atlas Pilot in native mode
# All other OSG_XXX are defined in the APF

#export OSG_APP=/cvmfs/osg.mwt2.org/connect/app
#export OSG_GRID=/cvmfs/osg.mwt2.org/osg/sw/osg-wn-client
#export OSG_WN_TMP=${_condor_LOCAL_DIR}/scratch
#export ATLAS_LOCAL_AREA=${OSG_APP}/atlas_app/local
#export X509_CERT_DIR=/cvmfs/osg.mwt2.org/osg/CA/certificates

# Make certain the OSG WN scratch exists
#mkdir -p ${OSG_WN_TMP}
#################


# And finally start the users job
exec "$@"

