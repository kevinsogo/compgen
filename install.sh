#!/bin/bash

set -e

chmod +x install.sh
cd scripts/
chmod +x all_files_subtasks convert_to_hackerrank direct_to_hackerrank hr subtasks_from_validator
sudo python2 setup.py install
sudo pypy setup.py install || echo setup for pypy failed... ignoring

echo DONE
