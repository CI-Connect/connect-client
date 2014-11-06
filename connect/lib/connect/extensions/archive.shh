#
# Create a debug archive
#

cd "$HOME"
tmpdir=".tmp.$$"
trap "rm -rf .tmp.$$" 0 1 2 3 15
user=$(whoami)

(
	arcdir="connect-debug.$user.$(date +%s)"
	mkdir -p "$tmpdir/$arcdir"
	cd "$tmpdir" || { echo >&2 "Cannot create debug archive!"; exit 255; }

	(
		echo Debug archive created at $(date)
		echo by $(id -a) @ $(hostname)
		echo
		env 2>&1 >$arcdir/environment
		# wtf? module list writes to stderr!
		module list 2>$arcdir/modules
		cp -pr $HOME/.bosco $arcdir/dotbosco 2>&1
		ps -fu $(whoami) 2>&1 >$arcdir/ps
	) >$arcdir/00log

	tar czf $HOME/$arcdir.tar.gz $arcdir &&
	echo "Debug archive created at $HOME/$arcdir.tar.gz ."
	echo "Please send this file to your support agent."
) || exit $?


