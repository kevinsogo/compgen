#!/usr/bin/python2

from __future__ import print_function

from sys import stderr
import os.path
from glob import glob

here = os.path.dirname(os.path.abspath(__file__))


template_suffix = '_TEMPLATE.md'


# replace
def get_replacements():
    for example in os.listdir(os.path.join(here, '..', 'examples')):
        base = os.path.join(here, '..', 'examples', example)
        if os.path.isdir(base):
            for pathname in sorted(glob(os.path.join(base, '*'))):
                if os.path.isfile(pathname):
                    with open(pathname) as f:
                        yield '{{{' + os.path.join(example, os.path.basename(pathname)) + '}}}', f.read().strip('\n')


replacements = list(get_replacements())

def get_templates():
    for dirpath, dirnames, filenames in os.walk(here):
        for filename in filenames:
            if filename.endswith(template_suffix):
                base = filename[:-len(template_suffix)]
                rel_dir = os.path.relpath(dirpath, here)
                rel_loc = os.path.join(rel_dir, filename)
                if rel_loc.startswith('./'): rel_loc = rel_loc[2:]
                yield os.path.join(dirpath, filename), os.path.join(here, '..', rel_dir, base + '.md'), rel_loc


for location, target, rel_loc in get_templates():
    print('DOING', location, target)
    with open(location) as f:
        s = f.read()

    # replace
    for old, new in replacements:
        s = s.replace(old, new)

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

    with open(target, 'w') as f:
        print("<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE; EDIT readme_src/{} INSTEAD, THEN RUN 'python2 gen_readme.py'. -->\n\n".format(rel_loc), file=f)
        f.write(s)

    # TODO possibly use a templating engine here instead of ad-hoc code
