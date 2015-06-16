#!/bin/sh

## Setup stuff.
## Actual installation steps are below.
## All these variables and functions are exposed to install.sub files.

# The Connect module loads python.  We install some python modules
# during build/installation, so we need to load python first to match
# python versions.
#
# XX Disable this for now: a site's default python version is not
# predictable, so we may end up loading Python 3 instead of Python 2.
# We'll just assume Py2 is in the environment already, and document
# the edge cases.
#module list >/dev/null 2>&1 &&
#module load python

from=$(dirname "$0")
siteinstall=false; export siteinstall

if [ "$1" = "-site" -o "$1" = "--site" ]; then
	siteinstall=true
	shift
fi

base="$1"
modlib="$2"
version="$3"

if [ -z "$base" -o "$base" = "-h" -o "$base" = "--help" ]; then
	echo >&2 "usage: $0 software-install-directory modulefiles-directory version"
	echo >&2
	echo >&2 "A software installation directory is required. If no modulefiles library"
	echo >&2 "is provided, a modulefile will be created in the installation directory."
	exit 2
fi

copyfiles () {
	rsync -a --exclude install.sub "$@"
}

status () {
	echo "[install]" "$@"
}

subinstall () {
	(
		cd "$1" &&
		. ./install.sub
	)
}


## Installation procedure:

cd $(dirname "$0")
mkdir -p "$base" 2>/dev/null
mkdir -p "$base/bin" 2>/dev/null

if [ ! -d "$base" ]; then
	echo >&2 "Cannot create $base - cannot install."
	exit 10
fi

# Install modulefiles
subinstall modules

# Install connect scripts
status Installing Connect user commands
subinstall connect

# tutorial has no install.sub because it's a subrepo
status ... tutorial command
# turns out this isn't useful because once python has the git module,
# it just runs git in a subprocess.
#sh scripts/tutorial/bundle-prereqs "$base" 2>&1 | sed -e 's/^/ | /'
copyfiles scripts/tutorial/tutorial "$base/bin/"
copyfiles scripts/distribution "$base/bin/"

# Install switch-module functions?
if $siteinstall; then
	subinstall switch-module
fi
