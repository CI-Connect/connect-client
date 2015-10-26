#!/bin/sh

# Find app dir
dir=$(dirname "$0")
cd "$dir"
cd ../..
dir=$(pwd)

# Link to app dir
cd $HOME
rm -f .ciconnect/macos
mkdir .ciconnect
ln -s "$dir/Contents/Resources" .ciconnect/macos

popup () {
	q='"'
	osascript -e "tell app ${q}Finder${q} to display dialog ${q}$*${q}"
}

# Check that app link is in path
cd "$HOME"
magic="connect client setup-1"
if grep "# $magic" .bashrc >/dev/null; then
	: ok
	popup "Your Connect Client installation has been updated."
else
	q='"'
	d='$'
	echo "PATH=$q$HOME/.ciconnect/macos/bin:${d}PATH$q # $magic" >>.bashrc
	popup "Your Connect Client installation has been located. You will need to quit and restart Terminal.app to use the connect command."
fi
