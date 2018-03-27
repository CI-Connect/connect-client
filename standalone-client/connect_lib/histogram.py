#!/usr/bin/env python
import os
import pwd


def whoami():
    pw = pwd.getpwuid(uid)
    return pw.pw_name


def show_histogram(args, config):
    """
    Display job histogram

    :return:
    """
    os.system('/usr/local/bin/job_histogram')