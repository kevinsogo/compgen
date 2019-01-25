#!/bin/bash

set -e

# make scripts executable
chmod +x setup.sh scripts/*

# python setup
pip3 install -U setuptools
pip3 install -U natsort

python3 setup.py install

echo DONE
