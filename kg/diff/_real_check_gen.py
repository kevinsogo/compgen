import os.path
from kg.black_magic import *

with open(os.path.join('templates', 'real_abs_rel_template.py')) as f:
    lines = [line.rstrip('\n') for line in f.readlines()]

for has_rel in [False, True]:
    for prec in range(16+1):
        filename = f'real_abs{"_rel"*has_rel}_1e_{prec}.py'
        print("Writing to", filename)
        with open(filename, 'w') as f:
            for line in compile_lines(lines,
                    has_rel=has_rel,
                    prec=prec,
                ):
                print(line, file=f)
