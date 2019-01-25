import argparse
import os.path
import os
import pathlib
import subprocess
import tempfile
from subprocess import Popen, PIPE, CalledProcessError
from collections import defaultdict
from string import ascii_letters

from .programs import *
from .formats import *
from .details import *
from .testscripts import *

def rec_ensure_exists(file):
    pathlib.Path(os.path.dirname(file)).mkdir(parents=True, exist_ok=True)











parser = argparse.ArgumentParser(description='There are many things you can do with this program.')
# TODO add 'verbose' option here
subparsers = parser.add_subparsers(help='which operation to perform', dest='main_command')
subparsers.required = True



# convert one format to another

convert_p = subparsers.add_parser('konvert', aliases=['convert'], help='convert help')
convert_p.add_argument('--from', nargs=2, help='source format and location', dest='fr')
convert_p.add_argument('--to', nargs=2, help='destination format and location')

def kg_convert(format_, args):
    if args.main_command == 'convert':
        print("You spelled 'konvert' incorrectly. Lucky for you, I'm merciful.", file=stderr)
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

subtasks_p = subparsers.add_parser('subtasks', help='detect the subtasks of input files. you need either a detector or a validator.')
subtasks_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
subtasks_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
subtasks_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
subtasks_p.add_argument('-i', '--input', help='input file pattern')
subtasks_p.add_argument('-o', '--output', help='output file pattern')
subtasks_p.add_argument('-c', '--command', nargs='+', help='detector command')
subtasks_p.add_argument('-f', '--file', help='detector file')
subtasks_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
subtasks_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command')
subtasks_p.add_argument('-vf', '--validator-file', help='validator file')

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

    get_subtasks(subtasks, detector, format_)

def get_subtasks(subtasks, detector, format_):
    subtset = set(subtasks)

    # iterate through inputs, run our detector against them
    subtasks_of = {}
    overall = set()
    detector.do_compile()
    inputs = []
    for input_ in format_.thru_inputs():
        inputs.append(input_)
        with open(input_) as f:
            result = detector.do_run(*subtasks, stdin=f, stdout=PIPE)
        subtasks_of[input_] = set(result.stdout.decode('utf-8').split())
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

    return subtasks_of, overall, inputs

subtasks_p.set_defaults(func=kg_subtasks)











# generate output data

gen_p = subparsers.add_parser('gen', help='generate output files for some given input files.')

gen_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
gen_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
gen_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
gen_p.add_argument('-i', '--input', help='input file pattern')
gen_p.add_argument('-o', '--output', help='output file pattern')
gen_p.add_argument('-c', '--command', nargs='+', help='solution command')
gen_p.add_argument('-f', '--file', help='solution file')
gen_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
gen_p.add_argument('-jf', '--judge-file', help='judge file')

def kg_gen(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i', write='o')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    solution = Program.from_args(args.file, args.command) or details.judge_data_maker
    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker

    _kg_gen(format_, solution, judge)

def _kg_gen(format_, solution, judge):
    if not solution: raise Exception("Missing solution")
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

test_p = subparsers.add_parser('test', help='test a program against given input and output files.')

test_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
test_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
test_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
test_p.add_argument('-i', '--input', help='input file pattern')
test_p.add_argument('-o', '--output', help='output file pattern')
test_p.add_argument('-c', '--command', nargs='+', help='solution command')
test_p.add_argument('-f', '--file', help='solution file')
test_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
test_p.add_argument('-jf', '--judge-file', help='judge file')
parser.add_argument('-js', '--judge-strict', action='store_true', help=argparse.SUPPRESS)# help="whether the checker is a bit too strict and doesn't work if extra arguments are given to it")

def kg_test(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='io')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    solution = Program.from_args(args.file, args.command) or details.model_solution
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
                    print(str(index).rjust(3), 'CHECKING AGAINST', input_)
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
        print(str(index).rjust(3), 'correct' if correct else 'WRONG!!!!!!!!!!')

    print('{} out of {} correct'.format(corrects, total))

    # TODO also print subtask grades

test_p.set_defaults(func=kg_test)






















# just run the solution

run_p = subparsers.add_parser('run', help='run a program against a set of input files, and print the result to stdout.')

run_p.add_argument('-F', '--format', '--fmt', default='kg', help='format of data')
run_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
run_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
run_p.add_argument('-i', '--input', help='input file pattern')
run_p.add_argument('-o', '--output', help='output file pattern')
run_p.add_argument('-c', '--command', nargs='+', help='solution command')
run_p.add_argument('-f', '--file', help='solution file')

def kg_run(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')

    details = Details()
    if is_same_format(args.format, 'kg'):
        details = Details.from_loc(args.details) or details

    solution = Program.from_args(args.file, args.command) or details.judge_data_maker
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





























# just run the solution

make_p = subparsers.add_parser('make', help='create all test data and validate.')

make_p.add_argument('makes', nargs='+', help='what to make. (all, inputs, etc.)')
make_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
make_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
make_p.add_argument('--validation', action='store_true', help="Validate the input files against the validators")
make_p.add_argument('--checks', action='store_true', help="Check the output file against the checker")

def kg_make(format_, args):
    if not is_same_format(format_, 'kg'):
        raise Exception("You can't use '{}' format to 'make'.".format(format_))


    details = Details()
    if is_same_format(format_, 'kg'):
        details = Details.from_loc(args.details) or details

    makes = set(args.makes)

    valid_makes = {'inputs', 'outputs', 'all', 'subtasks'}
    if not (makes <= valid_makes):
        raise Exception("Unknown make param(s): {}".format(' '.join(sorted(makes - valid_makes))))

    if 'all' in makes:
        makes |= valid_makes
        args.validation = args.checks = True

    if 'inputs' in makes:
        print('MAKING INPUTS...' + ("WITH VALIDATION..." if args.validation else 'WITHOUT VALIDATION'))
        if not details.testscript:
            raise Exception("Missing testscript")

        with open(details.testscript) as scrf:
            script = scrf.read()

        fmt = get_format_from_type(format_, args.loc, write='i')

        if args.validation:
            validator = details.validator
            validator.do_compile()

        for filename, gen, fargs in parse_testscript(fmt.thru_expected_inputs(), script, details.generators):
            print('GENERATING', filename)
            rec_ensure_exists(filename)
            gen.do_compile()
            with open(filename, 'w') as file:
                gen.do_run(*fargs, stdout=file)

            if args.validation:
                with open(filename) as file:
                    validator.do_run(stdin=file)

        print('DONE MAKING INPUTS.')


    if 'outputs' in makes:
        print('MAKING OUTPUTS...' + ("WITH CHECKER..." if args.checks else 'WITHOUT CHECKER'))
        fmt = get_format_from_type(format_, args.loc, read='i', write='o')
        _kg_gen(fmt, details.judge_data_maker, details.checker if args.checks else Program.noop())

        print('DONE MAKING OUTPUTS.')

    # TODO include subtasks creation and subtasks.json

    if 'subtasks' in makes:
        print('MAKING SUBTASKS...')
        subjson = details.subtasks_files
        if not subjson:
            raise Exception("subtasks_files entry in details is required at this step.")

        detector = details.subtask_detector
        if not detector: raise Exception("Missing detector/validator")

        # find subtask list
        subtasks = list(map(str, details.valid_subtasks))
        if details.validator and not subtasks: # subtask list required for detectors from validator
            raise Exception("Missing subtask list")

        # iterate through inputs, run our detector against them
        subtasks_of, overall, inputs = get_subtasks(subtasks, detector, get_format_from_type(format_, args.loc, read='i'))

        print('WRITING TO {}'.format(subjson))
        with open(subjson, 'w') as f:
            f.write('[\n' + '\n'.join('    {},'.format(str(list(x))) for x in construct_subs_files(subtasks_of, overall, inputs)).rstrip(',') + '\n]')

        print('DONE MAKING SUBTASKS.')



    print('SUCCESSFUL')

def construct_subs_files(subtasks_of, overall, inputs):
    prev = None
    lf = 0
    rg = -1
    for idx, file in enumerate(inputs):
        assert rg == idx - 1

        subs = subtasks_of[file]
        assert subs

        if prev != subs:
            assert (not prev) == (lf > rg)
            if prev:
                yield lf, rg, list(sorted(map(int, prev)))
            prev = subs
            lf = idx
        rg = idx
    if prev:
        yield lf, rg, list(sorted(map(int, prev)))

make_p.set_defaults(func=kg_make)













# make a new problem

init_p = subparsers.add_parser('init', help='create all test data and validate.')

init_p.add_argument('problemname', help='what to init. (all, inputs, etc.)')
init_p.add_argument('-l', '--loc', default='.', help='where to make the problem')

def kg_init(format_, args):
    if not is_same_format(format_, 'kg'):
        raise Exception("You can't use '{}' format to 'init'.".format(format_))
  
    prob = args.problemname

    if not set(prob) <= set(ascii_letters + '_-'):
        raise Exception("No special characters allowed for the problem name..")


    src = os.path.join(script_path, 'data', 'template')
    dest = os.path.join(args.loc, prob)

    print('making folder', dest)
    if os.path.exists(dest):
        raise Exception("The folder already exists!")

    env = {
        'problemtitle': ' '.join(re.split(r'[-_. ]+', prob)).title().strip(),
    }

    fmt = Format(os.path.join(src, '*'), os.path.join(dest, '*'), read='i', write='o')
    for inp, outp in fmt.thru_io():
        if not os.path.isfile(inp): continue
        rec_ensure_exists(outp)
        with open(inp) as inpf:
            with open(outp, 'w') as outpf:
                d = inpf.read()
                if inp.endswith('details.json'): d %= env
                outpf.write(d)

    print('DONE!')

init_p.set_defaults(func=kg_init)


def main(format):
    import sys
    args = parser.parse_args()
    args.func(format, args)
