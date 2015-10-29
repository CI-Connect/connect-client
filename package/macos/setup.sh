#!/bin/sh

# Find app dir
dir=$(dirname "$0")
cd "$dir"
cd ../..
dir=$(pwd)
resources="$dir/Contents/Resources"

# Link to app dir
cd $HOME
rm -f .ciconnect/macos
mkdir .ciconnect
ln -s "$resources" .ciconnect/macos

popup () {
	q='"'
	osascript -e "tell app ${q}Finder${q} to display dialog ${q}$*${q}"
}

# Check for newer version
getlatest () {
	dig connect-client.ci-connect.net txt \
	| awk -F'"' '/TXT/ && !/^;/ {print $2}' \
	| awk -F: '$1 == "latest-version" {print $2}'
}
latest=$(getlatest)
current=$(tr -d v < "$resources/version")
# even the keels by converting to equally padded numbers
ln=$(echo ${latest}00000 | tr -d . | cut -c-5)
cn=$(echo ${current}00000 | tr -d . | cut -c-5)
if [ "$ln" -eq "$cn" ]; then
	extra="Your client is up to date.\n"
elif [ "$ln" -gt "$cn" ]; then
	extra="A new Connect Client version is available at\nhttp://ci-connect.net/client .\n"
elif [ "$ln" -lt "$cn" ]; then
	extra="Your client is a pre-release version.\n"
fi

# Check that app link is in path
cd
magic="connect client setup-1"
if grep "# $magic" .profile >/dev/null; then
	: ok
	popup "Your Connect Client installation has been refreshed.\nCurrent version: $current (latest: $latest)\n$extra"
else
	q='"'
	d='$'
	echo "PATH=$q$HOME/.ciconnect/macos/bin:${d}PATH$q # $magic" >>.profile
	popup "Your Connect Client installation has been located. You will need to quit and restart Terminal.app to use the connect command.\n\nCurrent version: $current (latest: $latest)\n$extra"
fi
