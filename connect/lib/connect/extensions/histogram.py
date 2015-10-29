#!python


# We need to extend this to collect EITHER LastRemoteHost
# or MATCH_EXP_JOBGLIDEIN_ResourceName and match in the same table.
DOMAINMAP = '''
.*\?{8}                          *       [glidein]
qgp\d{2}                         *       duke/physics
lqcd\d{2}                        *       duke/physics
neutrino-\d{2}                   *       duke/physics
neuron-\d{2}                     *       duke/physics
neutron-\d{2}                    *       duke/physics
nano\d{2}                        *       duke/physics
compute-\d{2}-\d{2}\.local\d     *       uconn.edu
compute-\d-\d{2}.nysu\d          *       nysu?
nodo\d{2}                        *       cinvestav.mx
compute-\d-\d.local              atlas   swt2.org
compute-\d+-\d+.local            *       vt.edu
#computer?-\d+n?-\d+.tier2        *       compute-*.tier2
# Not sure this is unique, but at least some are caltech
computer?-\d+n?-\d+.tier2        *       caltech.edu
node\d{3}.local                  atlas   swt2.org
node\d{3}.local                  *       unesp.br
node\d{4}$                       *       clemson/palmetto
compute-\d-\d{2}.nys1            *       swt2.org
compute-\d-\d.nys1               *       swt2.org
compute-\d-\d{2}.local           *       swt2.org
golub\d{3}                       *       mwt2.org/illinois
taub\d{3}                        *       mwt2.org/illinois
iu.edu                           *       mwt2.org/indiana
uct2-c.*                         *       mwt2.org/chicago
midway\d{3}                      *       uchicago/rcc
midway-\d{3}-\d{2}               *       uchicago/rcc
uc3-.*.mwt2.org                  *       uchicago/uc3
.*-its-.*-nfs-\d{8}              *       syracuse/orangegrid
^CRUSH-OSG.*                     *       syracuse/orangegrid
r\w+-s\d+.ufhpc                  *       ufhpc            # e.g. r18a-s31.ufhpc

# This one is the wildcard catchall for domains: *.dom.ain -> dom.ain
.*\.([^.]*\.[^.]*)$              *       \\1
'''

import re

domainmap = []
for line in DOMAINMAP.strip().split('\n'):
	if '#' in line:
		line = line[:line.find('#')]
	if line == '':
		continue
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
	for rx, site, mapto in domainmap:
		m = rx.match(domain)
		if m:
			return rx.sub(mapto, domain)
	return domain

def last_cluster(user):
	# XXX wish I could do this via bindings
	iter = xsh('condor_history %s' % user)
	junk = iter.next()
	try:
		line = iter.next()
	except StopIteration:
		# no history
		return None
	w = line.split()
	return w[0].split('.')[0]

def usage():
	p = os.path.basename(sys.argv[0])
	yield '@ [-l | --last] [user]'

def run(*args):
	try:
		opts, args = getopt.getopt(args, 'l', ['last'])
	except getopt.GetoptError, e:
		print >>sys.stderr, str(e)
		return usage()

	lastjob = False
	for opt, arg in opts:
		if opt in ('-l', '--last'):
			lastjob = True

	if args:
		user = args[0]
	else:
		user = whoami()


	if lastjob:
		cluster = last_cluster(user)
		if cluster is None:
			print 'No recent jobs to report on.'
			return 10
		def source():
			cmd = "condor_history -format '%s\\n' LastRemoteHost " + str(cluster)
			for line in xsh(cmd):
				resource = line.split()[-1]
				yield resource

	else:
		def source():
			cmd = 'condor_q -run %s' % user
			for line in xsh(cmd):
				line = line.strip()
				if 'ID' in line:
					continue
				if 'Submitter' in line:
					continue
				if line == '':
					continue
				resource = line.split()[-1]
				yield resource

	brand = config.get('connect', 'brand')
	distr = os.popen('distribution --color --char=pb', 'w')
	for resource in source():
		if '@' in resource:
			slot, host = resource.strip().rsplit('@', 1)
		else:
			slot = ''
			host = resource
		domain = mapdomain(host, brand)
		distr.write(domain + '\n')
	distr.close()
