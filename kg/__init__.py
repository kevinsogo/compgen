import argparse
import os.path
import os
import pathlib
import subprocess
from subprocess import Popen, PIPE
from collections import defaultdict

from programs import *
from formats import *


def rec_ensure_exists(file):
    pathlib.Path(os.path.dirname(file)).mkdir(parents=True, exist_ok=True)



def kg_convert(format_, args):
    if not args.fr: raise Exception("Missing --from")
    if not args.to: raise Exception("Missing --to")

    src_format = get_format(argparse.Namespace(
            format=args.fr[0],
            loc=args.fr[1],
            input=None,
            output=None,
        ), read='io')

    dest_format = get_format(argparse.Namespace(
            format=args.to[0],
            loc=args.to[1],
            input=None,
            output=None,
        ), write='io')

    for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
        rec_ensure_exists(dsti)
        rec_ensure_exists(dsto)
        subprocess.call(['cp', srci, dsti])
        subprocess.call(['cp', srco, dsto])










def detector_from_validator(validator):
    return Program("!fromvalidator", validator.compile, ["kg-subtasks", "-c"] + validator.run + ["--"])

def kg_subtasks(format_, args):
    if args.format: args.format = format_

    detector = Program.from_args(args.file, args.command)
    if not detector:
        # try validator
        validator = Program.from_args(args.validator_file, args.validator_command)
        if validator:
            detector = detector_from_validator(validator)
            if not args.subtasks:
                raise Exception("Missing subtask list")

    if not detector:
        raise Exception("Missing detector/validator")

    ssub = set(args.subtasks)

    # iterate through inputs, run our detector against them
    format_ = get_format(args, read='i')
    subtasks = {}
    overall = set()
    for input_ in format_.thru_inputs():
        stdout, stderr = detector.do_run(*args.subtasks, inp=input_)
        subtasks[input_] = set(stdout.decode('utf-8').split())
        if not subtasks[input_]:
            raise Exception("No subtasks found for {}".format(input_))
        if ssub and not (subtasks[input_] <= ssub):
            raise Exception("Found invalid subtasks! {}".format(' '.join(sorted(subtasks[input_] - ssub))))

        overall |= subtasks[input_]
        print("Subtasks found for {}: {}".format(input_, ' '.join(sorted(subtasks[input_]))))

    if ssub:
        assert overall <= ssub
        if overall != ssub:
            print('Warning: Some subtasks not found: {}'.format(' '.join(sorted(ssub - overall))), file=stderr)
    
    print("Found subtasks: {}".format(' '.join(sorted(overall))))








parser = argparse.ArgumentParser(
        description='There are several commands.',
    )
subparsers = parser.add_subparsers(help='sub-command help')

convert_p = subparsers.add_parser('convert', help='convert help')
convert_p.add_argument('--from', nargs=2, help='source format and location', dest='fr')
convert_p.add_argument('--to', nargs=2, help='destination format and location')
convert_p.set_defaults(func=kg_convert)

subtasks_p = subparsers.add_parser('subtasks', help='subtasks help')
subtasks_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
subtasks_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
subtasks_p.add_argument('-d', '--details', default='details.json', help=argparse.SUPPRESS)
subtasks_p.add_argument('-i', '--input', help='input file pattern')
subtasks_p.add_argument('-o', '--output', help='output file pattern')
subtasks_p.add_argument('-c', '--command', nargs='+', help='detector command')
subtasks_p.add_argument('-f', '--file', help='detector program file')
subtasks_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
subtasks_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command')
subtasks_p.add_argument('-vf', '--validator-file', help='validator program file')
subtasks_p.set_defaults(func=kg_subtasks)

def main(format_):
    args = parser.parse_args()
    args.func(format_, args)


if __name__ == '__main__':
    main('kg')
