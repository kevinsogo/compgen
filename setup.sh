#!/bin/bash
set -e


# make scripts executable
chmod +x setup.sh docs_src/makedocs scripts/*

# TODO install pip3 here?
# easy_install pip or something

# install setuptools
python3 -m pip install --user setuptools

# install the 'kg' (and related) packages and dependencies.
python3 setup.py clean --all
python3 setup.py install


# also try installing for pypy3. (It should just skip if you don't have pypy3)
if [ -x "$(command -v pypy3)" ]; then
    echo "ATTEMPTING TO INSTALL ON pypy3"
    pypy3 -m ensurepip
    pypy3 -m pip install --user setuptools
    pypy3 setup.py clean --all
    pypy3 setup.py install
    echo "INSTALLED ON pypy3"
else
    echo "NOT INSTALLING ON pypy3, pypy3 NOT FOUND."
fi

echo "DONE"
