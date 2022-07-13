#!/bin/bash
set -e

# make scripts executable
chmod +x setup.sh docs/src/makedocs

# ensure pip is present
python3 -m ensurepip || echo "Can't run ensurepip. It is now your responsibility to ensure that pip is present!!!"

# install setuptools
python3 -m pip install --user setuptools
python3 -m pip install --user setupext-janitor

# install the 'kg' (and related) packages and dependencies.
python3 setup.py clean --all
python3 setup.py install --user
python3 setup.py clean --all

# also try installing for pypy3. (It should just skip if you don't have pypy3)
if [ -x "$(command -v pypy3)" ]; then
    echo "ATTEMPTING TO INSTALL ON pypy3 (sudo)"
    sudo pypy3 -m ensurepip
    sudo pypy3 -m pip install --user setuptools
    sudo pypy3 -m pip install --user setupext-janitor
    sudo pypy3 setup.py clean --all
    sudo pypy3 setup.py install --user
    sudo pypy3 setup.py clean --all
    echo "INSTALLED ON pypy3"
else
    echo "NOT INSTALLING ON pypy3, pypy3 NOT FOUND."
fi


echo
activate-global-python-argcomplete --user && echo "AUTOCOMPLETE READY" || echo "Skipping autocomplete"
echo "DONE"
