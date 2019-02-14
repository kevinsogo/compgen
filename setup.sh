#!/bin/bash
set -e


# make scripts executable
chmod +x setup.sh docs_src/makedocs scripts/*

# TODO install pip3 here?
# easy_install pip or something

# install setuptools
pip3 install -U setuptools

# install the 'kg' (and related) packages and dependencies.
python3 setup.py install


echo DONE
