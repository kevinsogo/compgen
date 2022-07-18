from collections import defaultdict
from glob import glob
from io import StringIO
from subprocess import PIPE
from sys import stdin, stderr
from textwrap import dedent
import argparse
import json
import os
import shutil
import tempfile

from .programs import get_python3_command, Program
from .utils import *

class KGAuxError(Exception): ...

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
        res = prog.do_run(sub, input=inp.encode('utf-8'), stderr=PIPE, stdout=PIPE, check=False, time=True, label='VALIDATOR')
        if res.result.returncode == 0:
            print(sub)
            if res.result.stdout: coll_out += f"[for subtask {sub}]\n{dec(res.result.stdout)}\n"
            if res.result.stderr: coll_err += f"[for subtask {sub}]\n{dec(res.result.stderr)}\n"

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
        raise KGAuxError(f'{args.filename} does not exist!')





noop_p = subparsers.add_parser('noop', help='Do nothing', description='Do nothing.')

@set_handler(noop_p)
def kgutil_noop(args):
    ...





cleartemps_p = subparsers.add_parser('clear-temp-files',
               help='Clear all kg temp files (files in the tempfile directory prefixed with "kg_tmp_")',
        description='Clear all kg temp files (files in the tempfile directory prefixed with "kg_tmp_").')

@set_handler(cleartemps_p)
def kgutil_cleartemps(args):
    temp_file_pat = os.path.join(tempfile.gettempdir(), 'kg_tmp_*')
    print(f"Removing files in: {temp_file_pat!r}", file=stderr)
    ct_file = 0
    ct_folder = 0
    for filename in glob(temp_file_pat):
        if os.path.isfile(filename):
            os.remove(filename)
            ct_file += 1
        else:
            shutil.rmtree(filename)
            ct_folder += 1
    print(f"Removed {ct_file} files and {ct_folder} folders", file=stderr)






mc_p = subparsers.add_parser('kg-main-commands', help='Print all main kg commands', description='Print all main kg commands.')

@set_handler(mc_p)
def kgutil_mc(args):
    print('kg', 'kg-pg', 'kg-polygon', 'kg-kg', 'kg-kompgen', 'kg-hr', 'kg-hackerrank')





oneindex_p = subparsers.add_parser('pg-1index',
         aliases=['1index', 'pg-oneindex', 'oneindex', 'pg-one-index', 'one-index'],
            help='Convert the subtasks file to use 1-indexing. (For polygon)',
     description='Convert the subtasks file to use 1-indexing. (For polygon)')
oneindex_p.add_argument('subtask_file', nargs='?', default='subtasks.json', help='The subtask file. Typically subtasks.json')

@set_handler(oneindex_p)
def kgutil_oneindex(args):
    with open(args.subtask_file) as f:
        subtasks_file = json.load(f)
    print()
    beginfo_print('The following list is one-indexed. Be careful.')
    print()

    files_of_subtask = defaultdict(set)
    subtset = set()
    for low, high, subs in subtasks_file:
        low += 1; high += 1
        subtset |= set(subs)
        if low > high: raise KGAuxError(f"Invalid range of files: {low} to {high}")
        for fileid in range(low, high + 1):
            for sub in subs:
                files_of_subtask[sub].add(fileid)
        print(info_text('The subtasks of files'), key_text(f'{low:4}'), info_text('to'), key_text(f'{high:4}'), info_text('are'), key_text(*subs))

    print()
    for sub in sorted(subtset):
        if files_of_subtask[sub]:
            deps = [dep for dep in sorted(subtset) if dep != sub and files_of_subtask[dep] <= files_of_subtask[sub]]
            print(info_text("Subtask"), key_text(sub), info_text("contains the ff subtasks:"), key_text(*deps))









##########################################
def main():
    args = parser.parse_args()
    args.handler(args)
