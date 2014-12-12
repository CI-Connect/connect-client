import getopt

def usage():
	yield '[-f | --full]'

def status(pool):
	if pool:
		cmd = 'condor_status -pool ' + pool
	else:
		cmd = 'condor_status'

	for line in xsh(cmd):
		yield line.rstrip()


def run(*args, **kwargs):
	try:
		opts, args = getopt.getopt(args, '?hf', ['help', 'full'])
	except getopt.GetoptError, e:
		error(str(e))

	full = False

	for opt, arg in opts:
		if opt in ('-?', '-h', '--help'):
			usage('[-f | --full]')
			return 0

		if opt in ('-f', '--full'):
			full = True

	# htcondor bindings, param object needs more dict methods :p
	pools = [x.strip() for x in param['flock_to'].split(',')]

	print 'Summary of available resources for all HTCondor pools:'
	print '    Total  Owner  Claimed  Unclaimed  Matched  Preempting'
	for pool in [None] + pools:
		if pool:
			print '===', pool, '==='
		else:
			print '=== LOCAL ==='

		if full:
			for line in status(pool):
				print line
		else:
			for line in status(pool):
				if 'Total' in line and 'Owner' not in line:
					vals = [x.strip() for x in line.replace('Total', '').split()]
					# as a list comprehension, vals is an iterator. Must
					# convert to list.
					print '    %5.5s  %5.5s  %7.7s  %9.9s  %7.7s  %10.10s' % tuple(vals[:6])


'''
if [[ "x$1" == "x-?" || "x$1" == "x-h" || "x$1" == "x--help" ]]; then
    echo "condor_status_all [ -f | --full]"
    exit 0
fi

if [[ "x$1" == "x-f" || "x$1" == "x--full" ]]; then
    FULL="yes"
fi

# ZEROFILL="yes"

POOLS=`condor_config_val flock_to`
#IFS=', ' read -a pools <<< "$POOLS"
arr=$(echo $POOLS | tr "," "\n")

function get_status {
    if [ "x$1" == "x" ]; then
        PARAM=""
    else
        PARAM="-pool $1"
    fi
    if [ ! -z $FULL ]; then
        condor_status $PARAM
    else
        #condor_status $PARAM | grep "Total" | grep -v "Owner" | sed "s/Total/Slots /"
        condor_status $PARAM | grep "Total" | grep -v "Owner" | sed "s/Total/     /"
        if [ $? ]; then
            [ -z $ZEROFILL ] || echo "                         0     0       0         0       0          0        0"
        fi
    fi
}
echo "Summary of available resources for all available HTCondor pools."
echo "                     Total Owner Claimed Unclaimed Matched Preempting Backfill"
echo "LOCAL POOL:"
get_status

#for i in "${array[@]}"
for i in $arr
do
    echo "POOL $i:"
    get_status $i
done
'''
