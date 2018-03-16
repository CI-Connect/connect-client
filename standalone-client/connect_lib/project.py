#!/usr/bin/env python

import os
import sys
import pwd
import grp
import string
import curses
import curses.panel
import getopt


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
            y, x, color = args
        else:
            y, x, color = 0, 0, curses.A_NORMAL
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
                    mode = curses.A_REVERSE | color
                else:
                    mode = curses.A_NORMAL | color
                msg = '%d. %s' % (index + 1, item)
                window.addstr(1 + index, 1, msg, mode)
            key = window.getch()
            if key in (curses.KEY_ENTER, ord('\n')):
                result = (self.position, self[self.position])
                break
            elif key == curses.KEY_UP:
                self.navigate(-1)
            elif key == 16:  # ^P
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
            elif key == 14:  # ^N
                self.navigate(1)
            # We can't quit on ESC because cursor movements
            # involve ESC on many terminals.
            # elif key == 27:		# ESCAPE
            #	break
            elif key == ord('Q'):
                break
            elif chr(key) in string.digits:
                self.navigate(key - ord('0'), rel=-1)
            elif chr(key) in string.ascii_letters:
                for i in range(0, len(self)):
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
    global CONFIG
    name = CONFIG.get('connect', 'name')

    if prompt is None:
        prompt = 'Select a project to be your default %s project.' % name

    if curses.has_colors():
        curses.use_default_colors()
    color = curses.A_NORMAL

    scr.addstr(0, 0, '%s Project Selector - %s' % (name, user.pw_name), color)
    scr.addstr(2, 0, prompt, color)
    scr.addstr(3, 0, 'Press "Q" to quit without changes.', color)
    scr.refresh()

    menu = Menu()
    menu.extend(projs)

    index, name = menu.display(scr, 5, 2, color)
    return index, name


def error(*args, **kwargs):
    fp = sys.stdout
    if 'fp' in kwargs:
        fp = kwargs['fp']
    fp.write("{0}".format(os.path.basename(sys.argv[0]) + ': ' + ' '.join(args)))


def update_project():
    global CONFIG

    user, projs = projects(None)

    fp = open(CONFIG.get('connect', 'blacklist'), 'r')
    blacklist = [x.strip() for x in fp.read().strip().split('\n')]
    fp.close()
    projs = [proj for proj in projs if proj not in blacklist]
    projs.sort(key=lambda x: x.lower())

    index, name = curses.wrapper(app, user, projs)

    if index is None:
        return 1

    # for condor_submit wrapper
    cfgdir = os.path.expanduser('~%s/.ciconnect' % user.pw_name)
    try:
        os.makedirs(cfgdir, mode=0o0700)
        os.chown(cfgdir, user.pw_uid, user.pw_gid)
    except OSError:
        pass
    fn = os.path.join(cfgdir, 'defaultproject')
    fp = open(fn, 'w')
    fp.write(name + '\n')
    fp.close()
    try:
        os.chown(fn, user.pw_uid, user.pw_gid)
    except OSError:
        pass

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
    try:
        os.chown(fn, user.pw_uid, user.pw_gid)
    except OSError:
        pass

    return 0


if __name__ == '__main__':
    try:
        sys.exit(update_project())
    except KeyboardInterrupt:
        sys.stdout.write('\ninterrupt')
        sys.exit(1)
