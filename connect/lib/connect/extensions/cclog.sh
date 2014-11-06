#
# connect client log
#

logfile="$HOME/.bosco/log/MasterLog"

isatty () {
	file="$1"
	[ -z "$file" ] && file=/dev/stdin

	# tty exits 0 if stdin is a tty, 1 if stdin is not a tty.
	# Redirect stdin from designated fd. That's not usable
	# for I/O but it gets us the info we need.
	tty <$file >/dev/null
}

isatty /dev/stdout && less $logfile || cat $logfile
