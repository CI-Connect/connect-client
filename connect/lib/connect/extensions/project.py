#!/usr/bin/env python

import os
import sys
import pwd
import grp
import string
import curses
import curses.panel
import getopt

def usage():
	yield '@'

# TODO: need a help keystroke

class Menu(list):
	# Loosely based on a solution by 'kalhartt' to
	# http://stackoverflow.com/questions/14200721/how-to-create-a-menu-and-submenus-in-python-curses

	def __init__(self, *args, **kwargs):
		list.__init__(self, *args, **kwargs)
		self.position = 0

	def navigate(self, n, rel=None):
		if rel is not None:
			self.position = rel + n
		else:
			self.position += n
		if self.position < 0:
			self.position += len(self)
		if self.position >= len(self):
			self.position -= len(self)

	def display(self, scr, *args):
		result = (None, None)
		if args:
			y, x = args
		else:
			y, x = 0, 0
		window = scr.subwin(y, x)
		window.keypad(1)
		panel = curses.panel.new_panel(window)
		panel.top()
		panel.show()
		window.clear()
		while True:
			window.refresh()
			curses.doupdate()
			for index, item in enumerate(self):
				if index == self.position:
					mode = curses.A_REVERSE | curses.color_pair(1)
				else:
					mode = curses.A_NORMAL | curses.color_pair(1)
				msg = '%d. %s' % (index + 1, item)
				window.addstr(1 + index, 1, msg, mode)
			key = window.getch()
			if key in (curses.KEY_ENTER, ord('\n')):
				result = (self.position, self[self.position])
				break
			elif key == curses.KEY_UP:
				self.navigate(-1)
			elif key == curses.KEY_DOWN:
				self.navigate(1)
			elif key == 27:		# ESCAPE
				break
			elif key == ord('Q'):
				break
			elif chr(key) in string.digits:
				self.navigate(key - ord('0'), rel=-1)
			elif chr(key) in string.letters:
				for i in xrange(0, len(self)):
					if self[i][0].lower() >= chr(key).lower():
						self.navigate(i, rel=0)
						break
			elif key == ord('\t'):
				self.navigate(5)

		window.clear()
		panel.hide()
		curses.panel.update_panels()
		curses.doupdate()

		return result


def groupmemberships(username):
	if username is None:
		user = pwd.getpwuid(os.getuid())
	else:
		user = pwd.getpwnam(username)
	groups = [g for g in grp.getgrall() if g.gr_name.startswith('@')]
	groups = [g for g in groups if user.pw_name in g.gr_mem]
	return user, groups


def projects(username):
	user, groups = groupmemberships(username)
	return user, [g.gr_name.lstrip('@') for g in groups]


def app(scr, user, projs, prompt=None):
	name = config.get('connect', 'name')

	if prompt is None:
		prompt = 'Select a project to be your default %s project.' % name

	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
	scr.addstr(0, 0, '%s Project Selector - %s' % (name, user.pw_name), curses.color_pair(1))
	scr.addstr(2, 0, prompt, curses.color_pair(1))
	scr.addstr(3, 0, 'Press ESCAPE or "Q" to quit without changes.', curses.color_pair(1))
	scr.refresh()

	menu = Menu()
	menu.extend(projs)

	index, name = menu.display(scr, 5, 2)
	return index, name


def error(*args, **kwargs):
	fp = sys.stdout
	if 'fp' in kwargs:
		fp = kwargs['fp']
	print >>fp, os.path.basename(sys.argv[0]) + ': ' + ' '.join(args)


def main(*args):
	job = False

	try:
		opts, args = getopt.getopt(args, 'j:', ['job'])
	except getopt.GetoptError, e:
		return error(str(e))

	for opt, arg in opts:
		if opt == '--job':
			job = True
		elif opt == '-j':
			if arg == 'ob':
				job = True
			else:
				return error('option', '-j' + arg, 'not recognized')

	if args:
		user, projs = projects(args[0])
	else:
		user, projs = projects(None)

	fp = open(config.get('connect', 'blacklist'), 'r')
	blacklist = [x.strip() for x in fp.read().strip().split('\n')]
	fp.close()
	projs = [proj for proj in projs if proj not in blacklist]
	projs.sort(lambda a, b: cmp(a.lower(), b.lower()))

	if job:
		index, name = curses.wrapper(app, user, projs, prompt='Select a project for this job to run under.')
	else:
		index, name = curses.wrapper(app, user, projs)

	if index is None:
		return 1

	if job:
		# write proj name to fd=9.  This is necessary because curses acts
		# on stdout, so using another fd or a static file is the only way
		# to capture the result from a shell.
		#
		# proj=$(connect project -j 9>&1)
		#
		fp = os.fdopen(9, 'w')
		fp.write(name)
		fp.close()
		return 0

	# Else update project files

	# attempt chown
	def chown(fn):
		try:
			os.chown(fn, user.pw_uid, user.pw_gid)
		except:
			pass

	# for condor_submit wrapper
	cfgdir = os.path.expanduser('~%s/.ciconnect' % user.pw_name)
	try:
		os.makedirs(cfgdir, mode=0700)
		chown(cfgdir)
	except:
		pass
	fn = os.path.join(cfgdir, 'defaultproject')
	fp = open(fn, 'w')
	fp.write(name + '\n')
	fp.close()
	chown(fn)

	# for finger
	fn = os.path.join(user.pw_dir, '.project')
	fp = open(fn, 'w')
	fp.write('Enabled in the following projects:\n')
	for proj in projs:
		if proj == name:
			fp.write('* ' + proj + ' (current)\n')
		else:
			fp.write('- ' + proj + '\n')
	fp.write('\n')
	fp.close()
	chown(fn)

	return 0


# make this work as a 'connect' extension
run = main

if __name__ == '__main__':
	try:
		sys.exit(main(*sys.argv[1:]))
	except KeyboardInterrupt:
		print '\ninterrupt'
		sys.exit(1)
