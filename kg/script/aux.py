from io import StringIO
from subprocess import PIPE
from sys import stdin, stderr
from textwrap import dedent
import argparse
import os

from .programs import get_python3_command, Program
from .utils import set_handler

class KGUtilError(Exception): ...

##########################################

# TODO use the 'logging' library

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Back-of-the-building scripts.')

subparsers = parser.add_subparsers(help='which operation to perform', dest='main_command')
subparsers.required = True





subtasks_p = subparsers.add_parser('subtasks-from-validator',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Detect subtasks from validator',
        description='Run against the validator across multiple subtasks and print those which accept.')
subtasks_p.add_argument('subs', nargs='+', help='List of subtasks')
subtasks_p.add_argument('-q', '--quiet', action='store_true', help=argparse.SUPPRESS)
subtasks_p.add_argument('-c', '--command', nargs='+', help='validator command', required=True)

@set_handler(subtasks_p)
def kg_subtasks(args):

    get_python3_command(verbose=not args.quiet)
    prog = Program.from_args(None, args.command)

    def dec(s):
        return s.decode('utf-8').rstrip('\n')

    inp = stdin.read()
    prog.do_compile()
    coll_out = ''
    coll_err = ''
    for sub in args.subs:
        res = prog.do_run(sub, input=inp.encode('utf-8'), stderr=PIPE, stdout=PIPE, check=False)
        if res.returncode == 0:
            print(sub)
            if res.stdout: coll_out += f"[for subtask {sub}]\n{dec(res.stdout)}\n"
            if res.stderr: coll_err += f"[for subtask {sub}]\n{dec(res.stderr)}\n"

    LEN = 1000
    if coll_out:
        print('Warning: the command', prog.run, 'outputted something in stdout.', file=stderr)
        print('It is recommended to not print anything if a validator accepts.', file=stderr)
        print('The following was printed in stdout:', file=stderr)
        print(coll_out[:LEN+3] if len(coll_out) <= LEN+3 else coll_out[:LEN] + '...', file=stderr)
    if coll_err:
        print('Warning: the command', prog.run, 'outputted something in stderr.', file=stderr)
        print('It is recommended to not print anything if a validator accepts.', file=stderr)
        print('The following was printed in stderr:', file=stderr)
        print(coll_err[:LEN+3] if len(coll_err) <= LEN+3 else coll_err[:LEN] + '...', file=stderr)



assertexist_p = subparsers.add_parser('assert-exist',
               help='Check if a file exists',
        description='Check if a file exists.')
assertexist_p.add_argument('filename', help='Filename to check')

@set_handler(assertexist_p)
def kgutil_assertexist(args):
    if not os.path.exists(args.filename):
        print(f'{args.filename} does not exist! This is bad...', file=stderr)
        raise KGUtilError(f'{args.filename} does not exist!')



noop_p = subparsers.add_parser('noop', help='Do nothing', description='Do nothing.')

@set_handler(noop_p)
def kgutil_noop(args):
    ...





##########################################
def main():
    args = parser.parse_args()
    args.handler(args)
