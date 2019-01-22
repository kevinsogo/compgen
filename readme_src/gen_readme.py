#!/usr/bin/python2

from __future__ import print_function

from sys import stderr
import os.path
from glob import glob

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README_TEMPLATE.md')) as f:
    s = f.read()

# replace
for pathname in sorted(glob(os.path.join(here, '..', 'examples', 'addition', '*'))):
    if os.path.isfile(pathname):
        with open(pathname) as f:
            s = s.replace('{{{' + os.path.basename(pathname) + '}}}', f.read().strip('\n'))

def first_ref(s, pos):
    i = s.find('{{{', pos)
    if i != -1:
        j = s.find('}}}', i)
        if j != -1:
            return (i, j), j

def find_refs(s):
    pos = 0
    while True:
        res = first_ref(s, pos)
        if not res: break
        (i, j), pos = res
        yield s[i: j+3]
        s = s[j+3:]


for found in find_refs(s):
    ref = repr(found)
    if len(ref) > 63:
        ref = ref[:30] + '...' + ref[-30:]
    print('WARNING: reference {} not found'.format(ref))

with open(os.path.join(here, '..', 'README.md'), 'w') as f:
    print("<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE; EDIT readme_src/README_TEMPLATE.md INSTEAD, THEN RUN 'python2 gen_readme.py'. -->\n\n", file=f)
    f.write(s)

# TODO possibly use a templating engine here instead of ad-hoc methods
