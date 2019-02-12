#!/bin/bash

set -e

# make scripts executable
chmod +x setup.sh docs_src/makedocs scripts/*

# install setuptools
pip3 install -U setuptools

# install the 'kg' (and related) packages and dependencies.
python3 setup.py install

echo DONE
