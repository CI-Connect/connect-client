#!/bin/sh

# Run ./build.sh to build all of the Docker images in this
# directory.

VERSION=$(sed -e 's/^v//' <../.version); export VERSION

docker build -t connect-client-base -f Dockerfile-base .
docker build -t connect-client-prep -f Dockerfile-prep .

sed -e "s,@@version@@,$VERSION,g" <Dockerfile-ready >tmp
docker build -t connect-client-ready:$VERSION -f tmp .
rm -f tmp
