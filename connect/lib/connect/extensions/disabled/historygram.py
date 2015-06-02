#!python

DOMAINMAP = '''
qgp\d{2}                         *       duke.edu
lqcd\d{2}                        *       duke.edu
neutrino-\d{2}                   *       duke.edu
neuron-\d{2}                     *       duke.edu
neutron-\d{2}                    *       duke.edu
nano\d{2}                        *       duke.edu
compute-\d{2}-\d{2}\.local\d     *       uconn.edu
compute-\d-\d{2}.nysu\d          *       uconn.edu
nodo\d{2}                        *       cinvestav.mx
compute-\d-\d.local              atlas   swt2.org
compute-\d-\d.local              *       vt.edu
node\d{3}.local                  atlas   swt2.org
node\d{3}.local                  *       unesp.br
compute-\d-\d{2}.nys1            *       swt2.org
compute-\d-\d.nys1               *       swt2.org
compute-\d-\d{2}.local           *       swt2.org
golub\d{3}                       *       mwt2.org
taub\d{3}                        *       mwt2.org
iu.edu                           *       mwt2.org
midway\d{3}                      *       rcc.uchicago.edu
midway-\d{3}-\d{2}               *       rcc.uchicago.edu
'''

import re

domainmap = []
for line in DOMAINMAP.strip().split('\n'):
	rx, site, mapto = [x.strip() for x in line.split()]
	rx = re.compile(rx, re.I)
	domainmap.append((rx, site, mapto))


def whoami():
	uid = 0

	while uid == 0:
		# Find the user via uid, unless it's root.
		uid = os.getuid()
		if uid > 0:
			break

		# Find the current user by getting the owner of the terminal.
		import pwd
		s = os.fstat(sys.stdin.fileno())
		uid = s.st_uid
		if uid > 0:
			break

		# Any other options?  If not, give up.
		break

	import pwd
	pw = pwd.getpwuid(uid)
	return pw.pw_name

def mapdomain(domain, site):
	for rx, mapsite, mapto in domainmap:
		if mapsite.lower() != site.lower() and mapsite != '*':
			continue
		m = rx.match(domain)
		if m:
			return rx.sub(mapto, domain)
	return domain

def last_cluster(user):
	# XXX wish I could do this via bindings
	try:
		iter = xsh('condor_history %s' % user)
		junk = iter.next()
		line = iter.next()
		iter.close()
	except StopIteration:
		return None
	w = line.split()
	return w[0].split('.')[0]

def run(*args):
	LAST = False

	try:
		opts, args = getopt.getopt(args, 'lh', ['last', 'help'])
	except getopt.GetoptError, e:
		error(str(e))
		return 2

	for opt, arg in opts:
		if opt in ('-l', '--last'):
			LAST = true
		if opt in ('-h', '--help'):
			usage('[-l | --last] {user | jobid}')
			return 2

	args = list(args)	# tuple to list

	if args:
		query = args.pop(0)
	else:
		query = whoami()
		LAST = True

	if LAST:
		query = last_cluster(query)

	if query == None:
		print >>sys.stderr, 'No historical jobs to analyze.'
		return 1

	distr = os.popen('distribution --color --char=pb', 'w')

	cmd = "condor_history -format '%s\\n' LastRemoteHost " + str(query)
	for line in xsh(cmd):
		slot, host = line.strip().rsplit('@', 1)
		parts = host.split('.')
		domain = '.'.join(parts[-2:])
		domain = mapdomain(domain, config.get('connect', 'brand'))
		distr.write(domain + '\n')
	distr.close()
