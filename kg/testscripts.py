import os.path

from .formats import *
from .programs import *

def find_matches(cmd, generators):
    for prog in generators:
        if prog.matches_abbr(cmd):
            yield prog


# for now, only accept "> $" commands
def parse_testscript(inputs, testscript, generators, relpath=None):
    for line in testscript.strip().split('\n'):
        parts = line.split()
        if not parts or parts[0] == '#':
            continue
        if parts[-2:] != ['>', '$']:
            raise Exception("Unsupported script line: {}".format(repr(line)))

        cmd = parts[:-2]

        if cmd[0] == '!':
            prog = Program.from_args('', cmd[1:], relpath=relpath)
            args = ''
        else:
            progs = list(find_matches(cmd[0], generators))
            if len(progs) >= 2:
                raise Exception("{} matches at least two programs! Please ensure that the base names of generators are unique.".format(cmd[0]))
            elif not progs:
                raise Exception("Couldn't find program {} (from {})".format(cmd[0], cmd))
            else:
                [prog] = progs
                args = cmd[1:]

        yield next(inputs), prog, args

