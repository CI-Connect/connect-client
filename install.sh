#!/bin/sh

## Setup stuff.
## Actual installation steps are below.
## All these variables and functions are exposed to install.sub files.

from=$(dirname "$0")
base="$1"
modlib="$2"

if [ -z "$base" -o "$base" = "-h" -o "$base" = "--help" ]; then
	echo >&2 "usage: $0 software-install-directory [modulefiles-directory]"
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

# Install bosco (connect client)
subinstall bosco

# Install connect scripts
status Installing Connect user commands
subinstall connect

# tutorial has no install.sub because it's a subrepo
status ... tutorial command
sh scripts/tutorial/bundle-prereqs "$base" 2>&1 | sed -e 's/^/ | /'
copyfiles scripts/tutorial/tutorial "$base/bin/"

# Install switch-module functions
subinstall switch-module
