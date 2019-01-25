#!/bin/bash

set -e

# make scripts executable
chmod +x setup.sh scripts/*

# python setup
pip3 install -U natsort
python3 setup.py install


# try setting up for pypy3 as well
pypy3 setup.py install || echo "setup for pypy3 failed... ignoring"

echo DONE
