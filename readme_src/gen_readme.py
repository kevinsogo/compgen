#!/usr/bin/python2

from __future__ import print_function

import os.path
from glob import glob

with open('README_TEMPLATE.md') as f:
    s = f.read()

# replace
for pathname in sorted(glob('../examples/addition/*')):
    if os.path.isfile(pathname):
        with open(pathname) as f:
            s = s.replace('{{{' + os.path.basename(pathname) + '}}}', f.read().strip('\n'))

with open('../README.md', 'w') as f:
    print("<!-- Note to contributors: Please don't edit this file; edit readme_src/README_TEMPLATE.md instead. -->\n\n", file=f)
    f.write(s)
