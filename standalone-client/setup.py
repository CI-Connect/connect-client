#!/usr/bin/env python

# Copyright 2015 University of Chicago
# Available under Apache 2.0 License
from distutils.core import setup

setup(name='connect_client',
      version='1.0.1',
      description='Scripts for connect client',
      url='https://github.com/CI-Connect/connect-client.git',
      packages=['connect_lib'],
      scripts=['connect'],
      license='Apache 2.0')


