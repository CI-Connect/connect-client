#!/bin/sh

# Simple startup command. This simply makes the session chdir
# to $HOME before running /bin/bash.

cd
exec /bin/bash
