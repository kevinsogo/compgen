import os.path

from .formats import *
from .programs import *

def find_matches(cmd, generators):
    for prog in generators:
        if prog.matches_abbr(cmd):
            yield prog


# for now, only accept "> $" commands
def parse_testscript(inputs, testscript, generators):
    for line in testscript.strip().split('\n'):
        parts = line.split()
        if not parts or parts[0] == '#':
            continue
        if parts[-2:] != ['>', '$']:
            raise Exception("Unsupported script line: {}".format(repr(line)))

        cmd = parts[:-2]

        if cmd[0] == '!':
            prog = Program('!custom', '', cmd[1:])
            args = ''
        else:
            progs = find_matches(cmd[0], generators)
            if len(progs) >= 2:
                raise Exception("{} matches at least two programs! Please ensure that the base names of generators are unique.".format(cmd[0]))
            elif not progs:
                raise Exception("Couldn't find program {} (from {})".format(cmd[0], cmd))
            else:
                [prog] = progs
                args = cmd[1:]

        yield next(inputs), prog, args













'''
Future ideas:

! cat sample.in > 1
single_case 10 10 > 2
single_case 10 100 > 3
single_case 10 1000 > $
single_case 10 10000 > $
multi_case [5-8,10] 10 1000 > {5-8,10}
multi_case_lazy 0 10 20 > $
multi_case_lazy 1 10 20 > $
multi_case_lazy 2 10 20 > $
multi_case_lazy 3 10 20 > $

... no templating (at least for now)
... replicate the way polygon tests work. (dollars and stuff)

formats:
12
{3,5-7,11}
{3,5-7,9..11} # either way is fine
{3,5-7,9..11,15..} # 15 to infinity
{3,5-7,9..11,15..+2} # 15 to infinity, incrementing by 2

[] or {} both allowable.



command > files

becomes

transformed_command > files
for each file in files; validate file.
'''

