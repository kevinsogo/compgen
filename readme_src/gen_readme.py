#!/usr/bin/python2

from __future__ import print_function

import os.path
from glob import glob

# TODO improve this so it's not dependent on where it's run

with open('README_TEMPLATE.md') as f:
    s = f.read()

# replace
for pathname in sorted(glob('../examples/addition/*')):
    if os.path.isfile(pathname):
        with open(pathname) as f:
            s = s.replace('{{{' + os.path.basename(pathname) + '}}}', f.read().strip('\n'))

with open('../README.md', 'w') as f:
    print("<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE; EDIT readme_src/README_TEMPLATE.md INSTEAD, THEN RUN 'python2 gen_readme.py'. -->\n\n", file=f)
    f.write(s)
