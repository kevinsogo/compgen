#!/usr/bin/python2

from __future__ import print_function

from sys import stderr
import os.path
from glob import glob

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README_TEMPLATE.md')) as f:
    s = f.read()

# replace
for example in os.listdir(os.path.join(here, '..', 'examples')):
    base = os.path.join(here, '..', 'examples', example)
    if os.path.isdir(base):
        for pathname in sorted(glob(os.path.join(base, '*'))):
            if os.path.isfile(pathname):
                with open(pathname) as f:
                    s = s.replace('{{{' + os.path.join(example, os.path.basename(pathname)) + '}}}', f.read().strip('\n'))

def next_ref(s, pos):
    i = s.find('{{{', pos)
    if i != -1:
        j = s.find('}}}', i)
        if j != -1:
            return (i, j+3), j+3

def find_refs(s):
    pos = 0
    while True:
        res = next_ref(s, pos)
        if not res: break
        (i, j), pos = res
        yield s[i: j]


for found in find_refs(s):
    ref = repr(found)
    if len(ref) > 63: ref = ref[:30] + '...' + ref[-30:]
    print('WARNING: reference {} not found'.format(ref))

with open(os.path.join(here, '..', 'README.md'), 'w') as f:
    print("<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE; EDIT readme_src/README_TEMPLATE.md INSTEAD, THEN RUN 'python2 gen_readme.py'. -->\n\n", file=f)
    f.write(s)

# TODO possibly use a templating engine here instead of ad-hoc code
