#!/bin/bash

set -e

# make scripts executable
chmod +x setup.sh docs_src/makedocs scripts/*

# python setup
pip3 install -U setuptools
pip3 install -U natsort
pip3 install -U colorama
pip3 install -U termcolor
pip3 install -U Jinja2

python3 setup.py install

echo DONE
