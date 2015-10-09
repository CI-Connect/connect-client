#!/bin/sh

# Run ./build.sh to build all of the Docker images in this
# directory.

for sub in base prep ready; do
	docker build -t $(basename $(pwd))-$sub -f Dockerfile-$sub .
done

