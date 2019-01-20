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


# var = 'kljashflskajhflksjahflskjahflsakjhfl'
var = 'yy'

file_command = '$(printf "input/input%02d.txt" ${})'.format(var)

print '''
#!/bin/bash
set -e
{}=0

'''.format(var)

for line in script.strip().split('\n'):
    if '$$$' in line:
        line = line.replace('$$$', file_command)
        indent = line[:len(line) - len(line.lstrip())]
        print line
        print indent + '{} < {}'.format(validator, file_command)
        print indent + '{var}=$(({var}+1))'.format(var=var)
    else:
        print line
