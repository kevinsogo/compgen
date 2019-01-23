#!/bin/bash

set -e

chmod +x install.sh readme_src/gen_readme.py
cd scripts/
chmod +x all_files_subtasks convert_to_hackerrank direct_to_hackerrank hr subtasks_from_validator polygonate hrate make_details
sudo python2 setup.py install
sudo pypy setup.py install || echo "setup for pypy failed... ignoring"

echo DONE
