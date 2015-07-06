#!/bin/sh

usage () {
	echo >&2 "usage: $0 version"
}

if [ "$1" = "" ]; then
	echo >&2 "no version given!"
	usage
	exit 2
fi

case "$1" in
	v*)	:
		;;
	*)	:
		echo >&2 "'$1' not a version string (must begin with 'v')"
		usage
		exit 2
		;;
esac

rel="$1"

dir=$(dirname "$0")
cd "$dir"
echo "$rel" >.version
git ci -m "tag release $rel" .version
git tag -a -m "release tag $rel" $rel
