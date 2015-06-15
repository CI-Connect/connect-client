#!/usr/bin/env python
#
# XXX TODO
#
# 1. use a uuid file to verify that local and remote project dirs match
#    * ${dir}/.uuid?
#    * store in a ~/.ciconnect/client/dirs.db?
#    * name remote dirs for the uuid itself? ~/connect-client/<uuid>
#
# 2. exchange() needs to handle multiple responses:
#    exchange('bla bla', {
#             403: handle_403,
#             200: handle_200,
#    })
#

import os
import sys
import getopt
import pwd
import socket
import getpass
import tempfile
import random
import time
import select
import uuid
import new
import urllib
import stat
import signal
import errno
import stat

_version = '@@version@@'

defaults = '''
[server]
staging = %(home)s
'''

def help():
	m = main()
	return m._help()


DEFAULT_CLIENT_SERVER = 'connect-client.osgconnect.net'

class GeneralException(Exception):
	def __iadd__(self, other):
		if isinstance(other, (str, unicode)):
			self.args = self.args + (other,)
		else:
			self.args = self.args + tuple(args)

	def bubble(self, *args):
		self.args = self.args + tuple(args)
		raise self


class SSHError(GeneralException): pass
class UsageError(GeneralException): pass


class codes(object):
	OK = 200
	MULTILINE = 201
	YES = 202
	WAT = 401
	NO = 402
	NOTPRESENT = 403
	FAILED = 404
	

def units(n):
	_ = 'bkmgtpezy'
	while n > 10240 and _:
		n /= 1024
		_ = _[1:]
	return '%.4g%s' % (n, _[0])


def cleanfn(fn):
	fn = os.path.normpath(fn)
	while True:
		if fn.startswith('/'):
			fn = fn.lstrip('/')
		elif fn.startswith('./'):
			fn = fn[2:]
		elif fn.startswith('../'):
			fn = fn[3:]
		else:
			break

	return fn


class ClientSession(object):
	remotecmd = ['connect', 'client', '--server-mode']

	def __init__(self, hostname, user=None, keyfile=None, password=None, debug=None, repo=None):
		self.hostname = hostname
		self.ssh = None
		self.version = 0
		self.transport = None
		self.channels = []
		self.user = user
		self.keyfile = keyfile
		self.password = password
		self.isdebug = False
		self.repo = repo

		if debug:
			self.debug = debug
			self.isdebug = True
		else:
			self.debug = lambda *args: True

		err = self.connect()
		if err:
			raise SSHError, 'Client authentication failed'
		if not self.ssh:
			raise SSHError, 'Client authentication failed'

		self.transport = self.ssh.get_transport()


	def connect(self):
		if self.user is None:
			self.user = getpass.getuser()
		if self.keyfile is None and self.password is None:
			self.password = getpass.getpass('Password for %s@%s: ' % (self.user, self.hostname))

		self.ssh = paramiko.SSHClient()
		self.ssh.load_system_host_keys()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		try:
			self.ssh.connect(self.hostname, username=self.user,
			                 password=self.password, key_filename=self.keyfile)
			return None
		except paramiko.AuthenticationException, e:
			return e
		except socket.gaierror, e:
			raise GeneralException, 'cannot connect to %s: %s' % (self.hostname, e.args[1])
		except IOError, e:
			if e.errno == errno.ENOENT:
				raise SSHError, 'No key file available.'
			raise


	def close(self):
		for channel in self.channels:
			channel.close()
		if self.ssh:
			pass #self.ssh.close()
		self.ssh = None


	def rcmd(self, args, server=False, remotedir=None):
		if server:
			args = self.remotecmd + args
		if self.repo:
			args = ['/usr/bin/env', 'JOBREPO=' + self.repo] + args
		cmd = ' '.join(["'" + x + "'" for x in args])

		if remotedir:
			cmd = ('[ -d "%s" ] && cd "%s"; ' % (remotedir, remotedir)) + cmd

		channel = self.transport.open_session()
		self.debug('client command: ' + cmd)
		channel.exec_command(cmd)
		channel.fp = channel.makefile()

		def _(**kwargs):
			return self.rio(channel, **kwargs)
		channel.rio = _

		def _(message, code, **kwargs):
			return self.exchange(channel, message, code, **kwargs)
		channel.exchange = _

		def _(*args, **kwargs):
			return self.pcmd(channel, *args, **kwargs)
		channel.pcmd = _

		def _(*args, **kwargs):
			return self.pgetline(channel, *args, **kwargs)
		channel.pgetline = _

		def _(*args, **kwargs):
			return self.preply(channel, *args, **kwargs)
		channel.preply = _

		self.channels.append(channel)
		return channel


	def handshake(self):
		if self.isdebug:
			channel = self.rcmd(['server', '-debug'], server=True)
		else:
			channel = self.rcmd(['server'], server=True)
		banner = channel.pgetline()
		if not banner.startswith('connect client protocol'):
			channel.close()
			raise SSHError, 'no connect sync server at server endpoint (closing)'

		self.version = int(banner.split()[3])
		channel.session = self
		return channel


	def rio(self, channel, stdin=True, stdout=True, stderr=True):
		'''I/O loop for remote command channels.'''
		# XXX may need to extend to support filters, etc.

		events = {}

		if stdin:
			def _():
				data = sys.stdin.read(1024)
				channel.send(data)
				return len(data)
			events[sys.stdin.fileno()] = _

		if stdout or stderr:
			def _():
				bytes = 0
				if stdout and channel.recv_ready():
					data = channel.recv(1024)
					sys.stdout.write(data)
					bytes += len(data)
				if stderr and channel.recv_stderr_ready():
					data = channel.recv_stderr(1024)
					sys.stderr.write(data)
					bytes += len(data)
				return bytes
			events[channel.fileno()] = _

		poll = select.poll()
		for fd in events:
			poll.register(fd, select.POLLIN)

		ready = True
		while ready:
			for fd, event in poll.poll():
				if event == select.POLLIN:
					if events[fd]() == 0:
						ready = False
						break
			sys.stdout.flush()


	def exchange(self, channel, message, code):
		channel.pcmd(message)
		data = []
		until = None
		while True:
			sys.stdout.flush()
			line = channel.pgetline()
			if until:
				if line == until:
					until = None
					return data
				else:
					data.append(line)
				continue

			args = line.split()
			rcode = int(args.pop(0))
			if rcode == code:
				return data
			elif rcode == codes.MULTILINE:
				if args:
					until = args[0]
				else:
					until = '.'
			else:
				raise SSHError, 'unexpected response %d %s' % (rcode, ' '.join(args))


	def pcmd(self, channel, *args):
		msg = ' '.join([str(x) for x in args])
		self.debug('>> ' + msg)
		return channel.send(msg + '\n')


	def pgetline(self, channel, split=False):
		msg = None
		while not msg:
			msg = channel.fp.readline()
			if msg == '':
				raise IOError, 'end of stream'
			msg = msg.strip()
			self.debug('<< ' + msg)

		if split:
			return msg.split()
		return msg


	def preply(self, channel, code, args):
		# are we even going to use this? not sure.
		return self.pcmd(channel, str(code), *args)


	def sftp(self):
		return paramiko.SFTPClient.from_transport(self.transport)


class Profile(object):
	def __init__(self, **kwargs):
		self.name = None
		self.user = None
		self.server = None
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __str__(self):
		return '[%s: user=%s, server=%s]' % \
		       (self.name, self.user, self.server)


class main(object):
	local = ' '.join([os.path.basename(sys.argv[0]), __name__])

	def __init__(self):
		self.name = os.path.basename(sys.argv[0])
		self.opts = []
		self.args = []
		self.mode = 'client'
		self.keybits = 2048
		self.session = None

		self.debug = lambda *args: True
		self.isdebug = False
		self.idletimeout = 5 * 60
		self.remotedir = None
		self.verbose = False

		# We'll put all the user/server contextual information
		# into a profile object:
		self.profile = Profile(name='builtin', server=None, user=None)

		# Go through some options for figuring out desired profile.
		# These are in PRIORITY ORDER. The first match wins.
		if self.profile.server is None:
			self.profile.server = os.environ.get('CONNECT_CLIENT_SERVER', None)

		if self.profile.user is None:
			self.profile.user = os.environ.get('CONNECT_CLIENT_USER', None)

		try:
			self.profile.name = config.get('client', 'profile')
			if self.profile.server is None:
				self.profile.server = config.get('clientprofiles',
				                                 self.profile.name + '.server')
			if self.profile.user is None:
				self.profile.user = config.get('clientprofiles',
				                               self.profile.name + '.user')
		except:
			# if anything went wrong, that's ok - we'll try the next thing
			pass

		if self.profile.server and '@' in self.profile.server:
			user, server = self.profile.server.split('@', 1)
			self.profile.server = server
			if self.profile.user is None:
				self.profile.user = user

		if self.profile.server is None:
			self.profile.server = DEFAULT_CLIENT_SERVER

		if self.profile.user is None:
			self.profile.user = getpass.getuser()

		# end profile stuff


	def _msg(self, fp, prefix, *args, **kwargs):
		if 'indent' in kwargs and kwargs['indent']:
			prefix = ' ' * len(prefix)

		if len(args) > 1:
			print >>fp, prefix + args[0] % args[1:]
		else:
			print >>fp, prefix + str(args[0])
		fp.flush()

	def error(self, *args, **kwargs):
		return self._msg(sys.stderr, 'error: ', *args, **kwargs)

	def notice(self, *args, **kwargs):
		return self._msg(sys.stdout, 'notice: ', *args, **kwargs)

	def _debug(self, *args, **kwargs):
		return self._msg(sys.stderr, '%s: ' % self.mode, *args, **kwargs)
	debug = lambda *args: True

	def output(self, *args):
		# XXX may want to use textwrap here (but not in error, notice).
		return self._msg(sys.stdout, '', *args)

	def _example_deco_without_args(f):
		def _(self, args):
			print self.name, args
			return f(self, args)
		return _

	def _example_deco_with_args(_args):
		def _(f):
			def _(self, args):
				print self.name, _args, args
				return f(self, args)
			return _
		return _

	def decorator(f):
		return f


	def hostname(self):
		return socket.gethostname()


	def ensure_dir(self, path, mode=0700):
		try:
			os.makedirs(path, mode)
		except:
			pass


	def path(self, *args):
		path = os.path.join(*args)
		if not os.path.isabs(path):
			path = os.path.join(os.path.expanduser('~'), path)
		return path


	def makeident(self):
		return self.profile.user + '@' + self.profile.server


	def ssh_keygen(self, ident=None, comment=None):
		import StringIO

		if not ident:
			ident = self.makeident()

		if not comment:
			comment = '(connect)'

		rsa = paramiko.rsakey.RSAKey.generate(self.keybits)
		fp = StringIO.StringIO()
		rsa.write_private_key(fp)
		key = fp.getvalue()
		fp.close()

		pub = 'ssh-rsa ' + rsa.get_base64() + ' ' + ident + ' ' + comment
		return ident, key, pub


	def unlink(self, file):
		try:
			os.unlink(file)
		except:
			pass


	def savefile(self, file, content, overwrite=False, mode=0600):
		fp = tempfile.NamedTemporaryFile(dir=os.path.dirname(file), delete=False)
		fp.write(content)
		fp.close()
		if not overwrite and os.path.exists(file):
			raise IOError, '"%s" exists' % file
		os.rename(fp.name, file)


	def readfile(self, file):
		fp = open(file, 'r')
		data = fp.read()
		fp.close()
		return data


	def keyfile(self, ident=None):
		if not ident:
			ident = self.makeident()
		return os.path.expanduser(os.path.join('~/.ssh/connect', ident))


	def sessionsetup(self):
		try:
			return ClientSession(self.profile.server, user=self.profile.user,
			                     keyfile=self.keyfile(),
			                     repo=os.path.basename(os.getcwd()),
			                     password='nopassword', debug=self.debug)
		except SSHError, e:
			e.bubble(
			    'You have no access to %s.' % self.profile.server,
			)


	def platforminfo(self):
		print '| Connect client version:', _version
		print '| Python version:', sys.version.replace('\n', '\n|   ')
		print '| Prefix:', sys.prefix
		print '| User profile:', self.profile
		print
		print 'System:'

		def sh(cmd):
			fp = os.popen(cmd, 'r')
			for line in fp:
				sys.stdout.write('| ' + line)
			fp.close()
		sh('uname -a')
		sh('uptime')
		sys.stdout.flush()


	def disabled_c_prototest(self, args):
		''''''

		session = self.sessionsetup()
		channel = session.handshake()

		local = os.getcwd()
		remote = os.path.basename(local)

		channel.exchange('dir %s create=yes' % remote, codes.OK)

		for i in xrange(5):
			x = random.randint(0, 100)
			channel.exchange('ping %d' % x, codes.OK)

		#data = channel.exchange('multitest foo', codes.OK)
		#print data

		# Offer some files
		for filename in ['ahoy.txt', 'xxatlas.sum']:
			# Initiate a push
			s = os.lstat(filename)
			channel.pcmd('want %s mtime=%d size=%d' % (self.fnencode(filename), s.st_mtime, s.st_size))
			args = channel.pgetline(split=True)
			rcode = int(args.pop(0))
			if rcode == codes.YES:
				# send
				pass

		# Request file list from server, and individual files
		data = channel.exchange('list', codes.OK)
		for line in data:
			args = line.strip().split()
			fn = self.fndecode(args.pop(0))
			attrs = self.attrs(args)
			if self.needfile(fn, attrs):
				# request file
				pass

		channel.exchange('quit', codes.OK)


	def push(self, channel, local=None):
		def awfulrecursivemkdir(sftp, dir):
			rel = '.'
			for part in dir.split('/'):
				rel = os.path.join(rel, part)
				try:
					rs = sftp.stat(rel)
				except:
					sftp.mkdir(rel)

		if local is None:
			local = os.getcwd()
		if self.remotedir is None:
			self.remotedir = os.path.basename(local)

		channel.exchange('dir %s create=yes' % self.remotedir, codes.OK)
		sftp = channel.session.sftp()

		basedir = os.getcwd()
		os.chdir(local)
		for root, dirs, files in os.walk('.'):
			for file in files + dirs:
				fn = os.path.join(root, file)
				fn = cleanfn(fn)
				# Initiate a push
				s = os.lstat(fn)
				channel.pcmd('want %s mtime=%d size=%d mode=0%04o' % (self.fnencode(fn), s.st_mtime, s.st_size, s.st_mode & 0777))
				args = channel.pgetline(split=True)
				rcode = int(args.pop(0))
				if rcode == codes.YES:
					# send
					rfn = os.path.join(self.remotedir, fn)
					awfulrecursivemkdir(sftp, os.path.dirname(rfn))
					if stat.S_ISDIR(s.st_mode):
						try:
							self.notice('sending %s/ as %s/...', fn, rfn)
							rs = sftp.stat(rfn)
						except:
							sftp.mkdir(rfn)
							pass
					else:
						try:
							self.notice('sending %s as %s...', fn, rfn)
							sftp.put(fn, rfn)
						except Exception, e:
							self.notice('while sending %s: %s', rfn, str(e))
					sftp.utime(rfn, (s.st_atime, s.st_mtime))
					sftp.chmod(rfn, s.st_mode)
					# do we need this? doesn't utime() handle it?
					channel.exchange('stime %s %d' % (self.fnencode(fn), s.st_mtime), codes.OK)

		os.chdir(basedir)


	def pull(self, channel, local=None):
		if local is None:
			local = os.getcwd()
		if self.remotedir is None:
			self.remotedir = os.path.basename(local)

		channel.exchange('dir %s' % self.remotedir, codes.OK)
		sftp = channel.session.sftp()

		basedir = os.getcwd()
		os.chdir(local)

		# Request file list from server, and individual files
		data = channel.exchange('list', codes.OK)
		for line in data:
			args = line.strip().split()
			fn = self.fndecode(args.pop(0))
			attrs = self.attrs(args)
			if self.needfile(fn, attrs):
				# request file
				rfn = os.path.join(self.remotedir, fn)
				dir = os.path.dirname(fn)
				self.ensure_dir(dir)
				self.notice('fetching %s as %s...', rfn, fn)
				sftp.get(rfn, fn)
				if 'mtime' in attrs:
					t = int(attrs['mtime'])
					os.utime(fn, (t, t))

		os.chdir(basedir)


	def sreply(self, code, *args):
		msg = str(code) + ' ' + ' '.join(args)
		self.debug('server: >> ' + msg)
		sys.stdout.write(msg + '\n')
		sys.stdout.flush()


	def attrs(self, args):
		attrs = {}
		for arg in args:
			if '=' not in arg:
				continue
			prop, val = arg.split('=', 1)
			attrs[prop.lower()] = val
		return attrs


	def needfile(self, file, attrs):
		try:
			s = os.lstat(file)
		except:
			return True

		if 'size' in attrs and s.st_size != int(attrs['size']):
			return True

		if 'mtime' in attrs and s.st_mtime < int(attrs['mtime']):
			return True

		if 'mode' in attrs and s.st_mode != int(attrs['mode'], base=8):
			return True

		return False


	def fnencode(self, fn):
		return urllib.quote_plus(fn)


	def fndecode(self, fn):
		return urllib.unquote_plus(fn)


	def usage(self):
		self.output('This is Connect Client v%s.' % _version)
		for line in self._help():
			if line.startswith('@ '):
				line = 'usage: %s %s' % (self.local, line[2:])
			self.output(line)

	def _help(self):
		yield '@ [opts] <subcommand> [args]'
		for attr in sorted(dir(self)):
			if attr.startswith('c_'):
				subcmd = attr[2:]
				driver = getattr(self, attr)
				yield '       %s [opts] %s %s' % (self.local, subcmd, driver.__doc__)
		yield ''
		yield 'opts:'
		yield '    -s|--server hostname       set connect server name'
		yield '    -u|--user username         set connect server user name'
		yield '    -r|--remote directory      set connect server directory name'
		yield '    -v|--verbose               show additional information'


	def __call__(self, args):
		args = list(args)
		try:
			r = getopt.getopt(args, 'u:ds:r:vh',
			                  ['server-mode', 'user=', 'debug', 'server=',
			                   'remote=', 'repo=', 'verbose', 'help'])
		except getopt.GetoptError, e:
			self.error(e)
			return 2

		self.opts, self.args = r

		for opt, arg in self.opts:
			if opt in ('--server-mode',):
				self.mode = 'server'

			if opt in ('-u', '--user'):
				self.profile.user = arg

			if opt in ('-d', '--debug'):
				self.debug = self._debug
				self.isdebug = True

			if opt in ('-s', '--server'):
				self.profile.server = arg

			if opt in ('-r', '--remote', '--repo'):
				self.remotedir = arg

			if opt in ('-v', '--verbose'):
				self.verbose = True

			if opt in ('-h', '--help'):
				self.usage()
				return 0

		if self.verbose:
			self.output('\nAdditional information:')
			self.platforminfo()
			print

		if len(self.args) == 0:
			self.usage()
			return 2

		if self.mode != 'server' and paramiko is None:
			self.error('%s %s requires the "paramiko" module for python%d.%d',
			           self.name, __name__, sys.version_info[0], sys.version_info[1])
			self.error('(try "pip install paramiko")')
			sys.exit(5)

		subcmd = self.args.pop(0)
		if self.mode == 'client':
			driver = 'c_' + subcmd
		else:
			driver = 's_' + subcmd

		try:
			driver = getattr(self, driver)
		except AttributeError:
			self.error('"%s" is not a valid subcommand. (Try %s -h.)',
			           subcmd, self.local)
			return 10

		if self.mode == 'server':
			# chdir to repo staging dir
			self.basedir = config.get('server', 'staging')
			self.repodir = None
			if 'JOBREPO' in os.environ:
				self.repodir = os.path.join(self.basedir, os.environ['JOBREPO'])
			else:
				raise ValueError, 'JOBREPO not set in environment'
			try:
				os.makedirs(self.basedir)
				os.makedirs(self.repodir)
			except:
				pass
			os.chdir(self.repodir)

		try:
			rc = driver(self.args)
		except SSHError, e:
			e.bubble('Did you run "%s setup"?' % self.local)
		except UsageError, e:
			e.bubble('usage: %s %s %s' % (self.local, subcmd, driver.__doc__))

		if self.session:
			self.session.close()
		return rc


	def c_setup(self, args):
		'''[--replace-keys] [--update-keys] [servername]'''

		overwrite = False
		update = False

		try:
			opts, args = getopt.getopt(args, '', ['replace-keys', 'update-keys'])
		except getopt.GetoptError, e:
			self.error(e)
			return 2

		for opt, arg in opts:
			if opt in ('--replace-keys',):
				overwrite = True
			if opt in ('--update-keys',):
				update = True

		if args:
			self.profile.server = args.pop(0)

		self.ensure_dir(self.path('.ssh/connect'))
		ident, key, pub = self.ssh_keygen()
		keyfile = self.keyfile()
		pubfile = keyfile + '.pub'

		if os.path.exists(keyfile) and os.path.exists(pubfile) and not overwrite:
			self.notice('You already have a setup key. (You may wish to run')
			self.notice('"%s setup --replace-keys" .)', self.local)
			return 20

		# If either pubfile or keyfile exists, it's missing its partner;
		# setting overwrite will fix it.  And if neither is present, overwrite
		# does no harm.
		overwrite = True

		try:
			self.savefile(keyfile, key, overwrite=overwrite)
			self.savefile(pubfile, pub, overwrite=overwrite)
		except IOError, e:
			self.error(e)
			self.error('(You may wish to run "%s setup --replace-keys" .)', self.local)
			return 20

		if update:
			oldkeyfile = self.keyfile().replace(self.profile.server, self.hostname())
			oldpubfile = oldkeyfile + '.pub'
			if os.path.exists(oldkeyfile) and os.path.exists(oldpubfile):
				os.rename(oldkeyfile, keyfile)
				os.rename(oldpubfile, pubfile)
				self.output('Keys updated.')
				return 0
			self.error('No keys could be updated.')
			return 21

		# expressly do not use a keyfile (prompt instead)
		try:
			session = ClientSession(self.profile.server,
			                        user=self.profile.user, keyfile=None,
			                        repo=os.path.basename(os.getcwd()),
			                        debug=self.debug)
		except SSHError, e:
			raise GeneralException, e.args

		channel = session.rcmd(['setup'], server=True, remotedir=self.remotedir)
		channel.send(pub + '\n')
		channel.send('.\n')
		channel.rio(stdin=False)
		channel.close()

		self.notice('Ongoing client access has been authorized at %s.',
		            self.profile.server)
		self.notice('Use "%s test" to verify access.', self.local)
		return 0


	def s_setup(self, args):
		'''--server-mode setup'''
		self.ensure_dir(self.path('.ssh'))
		fn = os.path.join('.ssh', 'authorized_keys')
		if os.path.exists(fn):
			authkeys = self.readfile(fn)
		else:
			authkeys = ''
		nauthkeys = authkeys

		while True:
			line = sys.stdin.readline()
			line = line.strip()
			if line == '.':
				break
			nauthkeys += line + '\n'

		if nauthkeys != authkeys:
			if os.path.exists(fn):
				os.rename(fn, fn + '.save')
			self.savefile(fn, nauthkeys, mode=0600, overwrite=True)

		return 0


	def c_echo(self, args):
		''' '''

		session = self.sessionsetup()
		channel = session.rcmd(['echo'], server=True, remotedir=self.remotedir)
		# we will do an echo test here later. For now, just echo at both ends.
		while True:
			buf = channel.recv(1024)
			if len(buf) <= 0:
				break
			sys.stdout.write(buf)
			sys.stdout.flush()

		return 0


	def s_echo(self, args):
		'''Echo everything in a loop.'''
		sys.stdout.write('Echo mode.\n')
		sys.stdout.flush()
		while True:
			buf = sys.stdin.read(1024)
			if len(buf) <= 0:
				break
			sys.stdout.write(buf)
			sys.stdout.flush()


	def c_test(self, args):
		''' '''

		if self.verbose:
			_verbose = 'verbose'
		else:
			_verbose = 'noverbose'

		# XXX TODO does not correctly detect when you can log in remotely,
		# but the client command is missing.
		code = str(random.randint(0, 1000))

		session = self.sessionsetup()
		channel = session.rcmd(['test', code, _verbose], server=True, remotedir=self.remotedir)
		test = ''
		while True:
			buf = channel.recv(1024)
			if len(buf) <= 0:
				break
			test += buf
		test = [x.strip() for x in test.strip().split('\n')]
		if code != test[0]:
			self.output('You have no access to %s. ' +
			            'Run "%s setup" to begin.', self.profile.server, self.local)
			return 10

		self.output('Success! Your client access to %s is working.', self.profile.server)
		if len(test) > 1:
			self.output('\nAdditional information:')
			for item in test[1:]:
				self.output(' * ' + item)
		return 0


	def s_test(self, args):
		'''Just an echo test to verify access to server.
		With verbose, print additional info.'''

		print args[0]
		sys.stdout.flush()
		if 'verbose' in args[1:]:
			self.platforminfo()
		return 0


	def s_server(self, args):
		debugfp = None
		if args and args[0] == '-debug':
			debugfp = open(os.path.expanduser('~/connect-server.log'), 'w')
			sys.stderr = debugfp
			def _(*args):
				if not args:
					return
				if '%' in args[0]:
					debugfp.write((args[0] % args[1:]) + '\n')
				else:
					debugfp.write(' '.join([str(x) for x in args]) + '\n')
				debugfp.flush()
			self.debug = _

		# hello banner / protocol magic
		sys.stdout.write('connect client protocol 1\n')
		sys.stdout.flush()

		recvfile = None
		idle = False

		def alrm(sig, ctx):
			idle = True
			sys.stderr.write('idle timeout\n')

		signal.signal(signal.SIGALRM, alrm)

		while not idle:
			# reset idle timer on each loop
			signal.alarm(self.idletimeout)

			line = sys.stdin.readline()
			if line == '':
				self.debug('hangup')
				break
			line = line.strip()
			if line == '':
				continue
			args = line.split()
			cmd = args.pop(0).lower()
			self.debug('server: <<', cmd, args)

			if cmd == 'quit':
				self.sreply(codes.OK, 'bye')
				break

			elif cmd == 'ping':
				self.sreply(codes.OK, 'pong', args[0])

			elif cmd == 'dir':
				dir = cleanfn(args.pop(0))
				attrs = self.attrs(args)
				os.chdir(basedir)
				try:
					os.chdir(dir)
					self.sreply(codes.OK, dir, 'ok')
				except:
					if 'create' in attrs and attrs['create'] == 'yes':
						try:
							os.makedirs(dir)
							os.chdir(dir)
							self.sreply(codes.OK, dir, 'created')
						except:
							self.sreply(codes.FAILED, dir, 'cannot create')
					else:
						self.sreply(codes.NOTPRESENT, dir, 'not present')

			elif cmd == 'multitest':
				endtag = 'end'
				self.sreply(codes.MULTILINE, endtag)
				sys.stdout.write('line 1 | %s\n' % line)
				sys.stdout.write('line 2 | %s\n' % line)
				sys.stdout.write('line 3 | %s\n' % line)
				sys.stdout.write('line 4 | %s\n' % line)
				sys.stdout.write(endtag + '\n')

			elif cmd == 'list':
				self.sreply(codes.MULTILINE)
				for root, dirs, files in os.walk('.'):
					for file in files:
						fn = os.path.join(root, file)
						fn = cleanfn(fn)
						s = os.lstat(fn)
						if not stat.S_ISREG(s.st_mode):
							continue
						sys.stdout.write('%s size=%d mtime=%d\n' % (
							self.fnencode(fn), s.st_size, s.st_mtime))
				sys.stdout.write('.\n')

			elif cmd == 'want':
				recvfile = cleanfn(self.fndecode(args.pop(0)))
				attrs = self.attrs(args)

				if self.needfile(recvfile, attrs):
					self.sreply(codes.YES, 'yes')
				else:
					self.sreply(codes.NO, 'no')

			elif cmd == 'stime':
				recvfile = cleanfn(self.fndecode(args.pop(0)))
				mtime = int(args[0])
				try:
					os.utime(recvfile, (mtime, mtime))
					self.sreply(codes.OK, '')
				except OSError, e:
					self.sreply(codes.FAILED, str(e))

			else:
				sys.stdout.write('%d unknown command %s\n' % (codes.WAT, cmd))

			sys.stdout.flush()

		sys.stdout.flush()
		if debugfp:
			debugfp.close()
		return 0


	#@decorator
	#def sync(f):
	#	'''Decorator that performs file sync before executing
	#	the wrapped fn.
	#	'''
	#	def _(self, args):
	#		self.push()
	#		self.pull()
	#		return f(self, args)
	#	return _


	def _submit(self, args, command='condor_submit'):
		'''<submitfile>'''

		session = self.sessionsetup()

		if self.remotedir is None:
			self.remotedir = os.path.basename(os.getcwd())

		# First push all files
		channel = session.handshake()
		self.push(channel)
		channel.exchange('quit', codes.OK)

		# Now run a submit
		channel = session.rcmd([command] + args, remotedir=self.remotedir)
		channel.rio()
		rc = channel.recv_exit_status()

		# Now pull all files
		channel = session.handshake()
		self.push(channel)
		channel.exchange('quit', codes.OK)

		# and close
		session.close()
		return rc


	def c_submit(self, args):
		'''<submitfile>'''
		return self._submit(args, command='condor_submit')


	def c_dag(self, args):
		'''<dagfile>'''
		return self._submit(args, command='condor_submit_dag')


	def c_push(self, args):
		'''[[localdir] remotedir]'''

		local = None
		if len(args) > 2:
			raise UsageError, 'too many arguments'
		if len(args) == 2:
			local, self.remotedir = args
		if len(args) == 1:
			self.remotedir, = args

		session = self.sessionsetup()
		channel = session.handshake()
		self.push(channel, local=local)
		channel.exchange('quit', codes.OK)


	def c_pull(self, args):
		'''[[localdir] remotedir]'''

		local = None
		if len(args) > 2:
			raise UsageError, 'too many arguments'
		if len(args) == 2:
			local, self.remotedir = args
		if len(args) == 1:
			self.remotedir, = args
			
		session = self.sessionsetup()
		channel = session.handshake()
		self.pull(channel, local=local)
		channel.exchange('quit', codes.OK)


	def c_sync(self, args):
		'''[[localdir] remotedir]'''

		local = None
		if len(args) > 2:
			raise UsageError, 'too many arguments'
		if len(args) == 2:
			local, self.remotedir = args
		if len(args) == 1:
			self.remotedir, = args

		session = self.sessionsetup()
		channel = session.handshake()
		self.pull(channel, local=local)
		self.push(channel, local=local)
		channel.exchange('quit', codes.OK)


	def c_revoke(self, args):
		''''''
		self.output('')
		self.output('This command -permanently- deletes the key used to authorize')
		self.output('access to your Connect servers from this client. You can')
		self.output('re-establish access using "%s setup". Is this' % self.local)
		yn = self.prompt('what you want [y/N]? ')
		self.output('')
		if yn.lower() not in ['y', 'yes']:
			self.output('Not revoking keys.')
			return

		try:
			os.unlink(self.keyfile())
			os.unlink(self.keyfile() + '.pub')
			self.notice('Key revoked.')
		except:
			self.notice('No keys to revoke!')


	def prompt(self, prompt):
		sys.stdout.write(prompt)
		sys.stdout.flush()
		r = sys.stdin.readline()
		return r.strip()

	# Creates a standard method that runs a remote shell command
	# indicated by _args.
	def _remoteshell(*_args):
		_args = list(_args)
		def _(self, args):
			session = ClientSession(self.profile.server,
			                        user=self.profile.user,
			                        keyfile=self.keyfile(),
			                        password='nopassword',
			                        repo=os.path.basename(os.getcwd()),
			                        debug=self.debug)

			if self.remotedir is None:
				self.remotedir = os.path.basename(os.getcwd())

			channel = session.rcmd(_args + args, remotedir=self.remotedir)
			channel.rio()
			rc = channel.recv_exit_status()
			session.close()
			return rc
		_.__doc__ = '<' + ' '.join(_args) + ' arguments>'
		return _

	# Creates a standard method that runs a remote connnect command.
	def _remoteconnect(*_args, **kwargs):
		min = None
		max = None
		opts = ''
		if 'min' in kwargs:
			min = kwargs['min']
		if 'max' in kwargs:
			max = kwargs['max']
		# TODO: opts should be more getopty
		if 'opts' in kwargs:
			opts = kwargs['opts']
		_args = list(_args)
		def _(self, args):
			if min and len(args) < min:
				raise UsageError, 'not enough arguments'
			if max and len(args) > max:
				raise UsageError, 'too many arguments'

			session = ClientSession(self.profile.server,
			                        user=self.profile.user,
			                        keyfile=self.keyfile(),
			                        password='nopassword',
			                        repo=os.path.basename(os.getcwd()),
			                        debug=self.debug)

			if self.remotedir is None:
				self.remotedir = os.path.basename(os.getcwd())

			channel = session.rcmd(_args + args, remotedir=self.remotedir, server=True)
			channel.rio()
			rc = channel.recv_exit_status()
			session.close()
			return rc
		_.__doc__ = opts
		return _

	# These are simple, transparent commands -- no more complexity
	# than 'ssh server cmd args'.
	c_q = _remoteshell('condor_q')
	c_rm = _remoteshell('condor_rm')
	c_history = _remoteshell('condor_history')
	c_run = _remoteshell('condor_run')
	c_wait = _remoteshell('condor_wait')

	# XXX need to store default pool name in local config for status
	c_status = _remoteshell('condor_status')

	# These are direct remote procedure calls to server-mode methods.
	# E.g., if c_xyz = _remoteconnect('abc') then 'connect client xyz'
	# will invoke s_xyz() at the server.
	c_list = _remoteconnect('list', opts='[-v]')
	c_where = _remoteconnect('where', max=0)


	def s_list(self, args):
		# List job repos in this dir
		# TODO: should check for job uuid (juid)
		# TODO: some interactive logic to flag out-of-sync repos

		def getsize(path):
			size = 0
			nfiles = 0
			for root, files, dirs in os.walk(path):
				nfiles += len(files)
				for file in files:
					s = os.stat(os.path.join(root, file))
					size += s.st_size
			return nfiles, size

		for entry in sorted(os.listdir(self.basedir)):
			path = os.path.join(self.basedir, entry)
			if entry.startswith('.'):
				continue
			if os.path.islink(path):
				continue
			if not os.path.isdir(path):
				continue
			if '-v' in args:
				nfiles, size = getsize(path)
				print '%s   [%d files, %s total]' % (entry, nfiles, units(size))
			else:
				print entry
			sys.stdout.flush()


	def s_where(self, args):
		print self.repodir


# consider using rsync implementation by Isis Lovecruft at
# https://github.com/isislovecruft/pyrsync

def run(*args, **kwargs):
	m = main()
	try:
		sys.exit(m(args))

	except KeyboardInterrupt:
		print '\nbreak'
		sys.exit(1)

	except Exception, e:
		if m.isdebug:
			raise
		#m.error('%s ("%s --debug" to diagnose):',
		#           e.__class__.__name__, m.local)
		#for i, arg in enumerate(e.args):
		#	m.error(arg, indent=(i>0))
		m.error(e.__class__.__name__ + ': ' + str(e.args[0]))
		for arg in e.args[1:]:
			m.error(arg)
		sys.exit(10)


try:
	# Paramiko may be built using an older libgmp, but we can't
	# do anything about that.  Suppress this warning.
	import warnings
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		import paramiko
except ImportError:
	paramiko = None


if __name__ == '__main__':
	run(*sys.argv[1:])
