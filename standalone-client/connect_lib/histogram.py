#!/usr/bin/env python
import getopt
import os
import pwd
import sys


def whoami():
    pw = pwd.getpwuid(uid)
    return pw.pw_name


def show_histogram():
    """
    Display job histogram

    :return:
    """
    os.system('/usr/local/bin/job_histogram')