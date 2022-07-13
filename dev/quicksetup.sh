#!/bin/bash

# run as 'dev/quicksetup.sh'

set -e

# make scripts executable
chmod +x setup.sh docs/src/makedocs

python3 setup.py install --user
python3 setup.py clean --all

echo
activate-global-python-argcomplete --user && echo "AUTOCOMPLETE READY" || echo "Skipping autocomplete"
echo "DONE"
