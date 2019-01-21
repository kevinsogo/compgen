from sys import argv, stderr

with open(argv[1]) as f:
    script = f.read()

validator = argv[2]

if '$$$$' in script:
    print >>stderr, 'Invalid testset script: must not contain $$$$'
    exit(1)

if '$$$' not in script:
    print >>stderr, 'Invalid testset script: must contain $$$'
    exit(1)

for line in script:
    if line.count('$$$') >= 2:
        print >>stderr, 'Invalid testset script: each line can only have at most one $$$'
        exit(1)


fctr = 'kljashflskajhflksjahflskjahflsakjhfl'
fname = 'slkdfjsdafsdifoidsafuoisdoidoioiioo'


print '''#!/bin/bash
set -e
{fctr}=0

'''.format(fctr=fctr)

for line in script.strip().split('\n'):
    if '$$$' in line:
        line = line.replace('$$$', '$' + fname)
        indent = line[:len(line) - len(line.lstrip())]
        print indent + '{fname}=$(printf "input/input%02d.txt" ${fctr})'.format(fctr=fctr, fname=fname)
        print indent + '{fctr}=$(({fctr}+1))'.format(fctr=fctr)
        print line
        print indent + '{} < ${fname}'.format(validator, fname=fname)
    else:
        print line
