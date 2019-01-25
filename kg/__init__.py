import argparse
import os.path
import os
import pathlib
import subprocess
import tempfile
from subprocess import Popen, PIPE, CalledProcessError
from collections import defaultdict

from programs import *
from formats import *
from details import *

def rec_ensure_exists(file):
    pathlib.Path(os.path.dirname(file)).mkdir(parents=True, exist_ok=True)











parser = argparse.ArgumentParser(description='There are several commands.')
# TODO add 'verbose' option here
subparsers = parser.add_subparsers(help='sub-command help')




# convert one format to another

convert_p = subparsers.add_parser('convert', help='convert help')
convert_p.add_argument('--from', nargs=2, help='source format and location', dest='fr')
convert_p.add_argument('--to', nargs=2, help='destination format and location')

def kg_convert(format_, args):
    if not args.fr: raise Exception("Missing --from")
    if not args.to: raise Exception("Missing --to")

    src_format = get_format(argparse.Namespace(format=args.fr[0], loc=args.fr[1], input=None, output=None), read='io')
    dest_format = get_format(argparse.Namespace(format=args.to[0], loc=args.to[1], input=None, output=None), write='io')

    for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
        rec_ensure_exists(dsti)
        rec_ensure_exists(dsto)
        subprocess.call(['cp', srci, dsti])
        subprocess.call(['cp', srco, dsto])

convert_p.set_defaults(func=kg_convert)










# detect subtasks

subtasks_p = subparsers.add_parser('subtasks', help='subtasks help')
subtasks_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
subtasks_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
subtasks_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
subtasks_p.add_argument('-i', '--input', help='input file pattern')
subtasks_p.add_argument('-o', '--output', help='output file pattern')
subtasks_p.add_argument('-c', '--command', nargs='+', help='detector command')
subtasks_p.add_argument('-f', '--file', help='detector program file')
subtasks_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
subtasks_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command')
subtasks_p.add_argument('-vf', '--validator-file', help='validator program file')

def kg_subtasks(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    validator = None
    detector = Program.from_args(args.file, args.command)

    if not detector: # try validator
        validator = Program.from_args(args.validator_file, args.validator_command)
        detector = detector_from_validator(validator)
        assert (not detector) == (not validator)

    # try detector from details
    if not detector: detector = details.subtask_detector

    # can't build any detector!
    if not detector: raise Exception("Missing detector/validator")

    # find subtask list
    subtasks = args.subtasks or list(map(str, details.valid_subtasks))

    if validator and not subtasks: # subtask list required for detectors from validator
        raise Exception("Missing subtask list")

    subtset = set(subtasks)

    # iterate through inputs, run our detector against them
    subtasks_of = {}
    overall = set()
    detector.do_compile()
    for input_ in format_.thru_inputs():
        with open(input_) as f:
            result = detector.do_run(*subtasks, stdin=f, stdout=PIPE)
            stdout, stderr = runner.communicate()
            if runner.returncode: exit(returncode)
        subtasks_of[input_] = set(stdout.decode('utf-8').split())
        if not subtasks_of[input_]:
            raise Exception("No subtasks found for {}".format(input_))
        if subtset and not (subtasks_of[input_] <= subtset):
            raise Exception("Found invalid subtasks! {}".format(' '.join(sorted(subtasks_of[input_] - subtset))))

        overall |= subtasks_of[input_]
        print("Subtasks found for {}: {}".format(input_, ' '.join(sorted(subtasks_of[input_]))))

    print("Found subtasks: {}".format(' '.join(sorted(overall))))

    if subtset:
        assert overall <= subtset
        if overall != subtset:
            print('Warning: Some subtasks not found: {}'.format(' '.join(sorted(subtset - overall))), file=stderr)

subtasks_p.set_defaults(func=kg_subtasks)











# generate output data

gen_p = subparsers.add_parser('gen', help='help for "gen"')

gen_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
gen_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
gen_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
gen_p.add_argument('-i', '--input', help='input file pattern')
gen_p.add_argument('-o', '--output', help='output file pattern')
gen_p.add_argument('-c', '--command', nargs='+', help='solution command')
gen_p.add_argument('-f', '--file', help='solution program file')
gen_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
gen_p.add_argument('-jf', '--judge-file', help='judge program file')

def kg_gen(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i', write='o')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    solution = Program.from_args(args.file, args.command) or details.judge_data_runner
    if not solution: raise Exception("Missing solution")

    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker
    if not judge: raise Exception("Missing judge")

    solution.do_compile()
    judge.do_compile()
    for input_, output_ in format_.thru_io():
        rec_ensure_exists(output_)
        with open(input_) as inp:
            with open(output_, 'w') as outp:
                print('WRITING', input_, '-->', output_)
                try:
                    solution.do_run(stdin=inp, stdout=outp, time=True)
                except CalledProcessError as cpe:
                    print("The solution raised an error for {}".format(input_), file=stderr)
                    exit(cpe.returncode)

        # check with judge
        try:
            judge.do_run(input_, output_, output_)
        except CalledProcessError as cpe:
            print("The judge did not accept {}".format(output_), file=stderr)
            exit(cpe.returncode)


gen_p.set_defaults(func=kg_gen)












# generate output data

test_p = subparsers.add_parser('test', help='help for "test"')

test_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
test_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
test_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
test_p.add_argument('-i', '--input', help='input file pattern')
test_p.add_argument('-o', '--output', help='output file pattern')
test_p.add_argument('-c', '--command', nargs='+', help='solution command')
test_p.add_argument('-f', '--file', help='solution program file')
test_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
test_p.add_argument('-jf', '--judge-file', help='judge program file')
parser.add_argument('-js', '--judge-strict', action='store_true', help=argparse.SUPPRESS)# help="whether the checker is a bit too strict and doesn't work if extra arguments are given to it")

def kg_test(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='io')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    solution = Program.from_args(args.file, args.command) or details.judge_data_runner
    if not solution: raise Exception("Missing solution")

    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker
    if not judge: raise Exception("Missing judge")

    solution.do_compile()
    judge.do_compile()
    total = corrects = 0
    for index, (input_, output_) in enumerate(format_.thru_io()):
        def check_correct():
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                with open(input_) as inp:
                    print('CHECKING AGAINST', input_)
                    try:
                        solution.do_run(stdin=inp, stdout=tmp, time=True)
                    except CalledProcessError:
                        print('The solution issued a runtime error...')
                        return False

                jargs = [input_, tmp.name, output_]
                if not args.judge_strict:
                    jargs += ['-c', solution.filename, '-t', str(index), '-v']

                return judge.do_run(*jargs, check=False).returncode == 0

        correct = check_correct()
        total += 1
        corrects += correct
        print('correct' if correct else 'WRONG!!!!!!!!!!')

    print('{} out of {} correct'.format(corrects, total))

test_p.set_defaults(func=kg_test)






















# generate output data

run_p = subparsers.add_parser('run', help='help for "run"')

run_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
run_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
run_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
run_p.add_argument('-i', '--input', help='input file pattern')
run_p.add_argument('-o', '--output', help='output file pattern')
run_p.add_argument('-c', '--command', nargs='+', help='solution command')
run_p.add_argument('-f', '--file', help='solution program file')

def kg_run(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    solution = Program.from_args(args.file, args.command) or details.judge_data_runner
    if not solution: raise Exception("Missing solution")

    solution.do_compile()
    for input_ in format_.thru_inputs():
        with open(input_) as inp:
            print('RUNNING FOR', input_, file=stderr)
            try:
                solution.do_run(stdin=inp, time=True)
            except CalledProcessError:
                print('The solution issued a runtime error...', file=stderr)


run_p.set_defaults(func=kg_run)























def main(format_):
    args = parser.parse_args()
    args.func(format_, args)

if __name__ == '__main__':
    main('kg')
