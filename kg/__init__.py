from collections import defaultdict
from datetime import datetime
from functools import wraps
from html.parser import HTMLParser
from operator import attrgetter
from random import randrange
from shutil import copyfile
from string import ascii_letters, ascii_uppercase, digits
from subprocess import Popen, PIPE, CalledProcessError
from sys import *
import argparse
import os.path
import re
import tempfile
import zipfile

from natsort import natsorted

from .black_magic import *
from .contest_details import *
from .details import *
from .formats import *
from .iutils import *
from .passwords import *
from .programs import *
from .seating import *
from .testscripts import *
from .utils import *


class CommandException(Exception): ...





##########################################

# TODO use the 'logging' library

parser = argparse.ArgumentParser(description='There are many things you can do with this program.')
# TODO add 'verbose' option here
subparsers = parser.add_subparsers(help='which operation to perform', dest='main_command')
subparsers.required = True





##########################################
# convert one format to another

convert_p = subparsers.add_parser('konvert', aliases=['convert'], help='Convert test data from one format to another')
convert_p.add_argument('--from', nargs=2, help='source format and location', dest='fr', metavar=('FROM_FORMAT', 'FROM_FOLDER'), required=True)
convert_p.add_argument('--to', nargs=2, help='destination format and location', metavar=('TO_FORMAT', 'TO_FOLDER'), required=True)

@set_handler(convert_p)
def kg_convert(format_, args):
    if args.main_command == 'convert':
        print("You spelled 'konvert' incorrectly. I'll let it slide for now.", file=stderr)
    
    convert_formats(args.fr, args.to)

def convert_formats(src, dest):
    sformat, sloc = src
    dformat, dloc = dest
    src_format = get_format(argparse.Namespace(format=sformat, loc=sloc, input=None, output=None), read='io')
    dest_format = get_format(argparse.Namespace(format=dformat, loc=dloc, input=None, output=None), write='io')

    copied = 0
    print("Copying now...")
    for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
        touch_container(dsti)
        touch_container(dsto)
        copyfile(srci, dsti)
        copyfile(srco, dsto)
        copied += 2
    print("Copied", copied, "files")





##########################################
# convert one file sequence to another

convert2_p = subparsers.add_parser('konvertsequence', aliases=['convertsequence'], help='Convert a file sequence with a certain pattern to another.')
convert2_p.add_argument('--from', help='source file pattern', dest='fr', required=True)
convert2_p.add_argument('--to', help='destination file pattern', required=True)

@set_handler(convert2_p)
def kg_convert2(format_, args):
    if args.main_command == 'convertsequence':
        print("You spelled 'konvertsequence' incorrectly. I'll let it slide for now.", file=stderr)

    convert_sequence(args.fr, args.to)

def convert_sequence(src, dest):
    format_ = get_format(argparse.Namespace(format=None, loc=None, input=src, output=dest), read='i', write='o')

    copied = 0
    print("Copying now...")
    for srcf, destf in format_.thru_io():
        touch_container(destf)
        copyfile(srcf, destf)
        copied += 1
    print("Copied", copied, "files")





##########################################
# detect subtasks

subtasks_p = subparsers.add_parser('subtasks', help='detect the subtasks of input files. you need either a detector or a validator.')
subtasks_p.add_argument('-F', '--format', '--fmt', help='format of data')
subtasks_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
subtasks_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
subtasks_p.add_argument('-i', '--input', help='input file pattern')
subtasks_p.add_argument('-o', '--output', help='output file pattern')
subtasks_p.add_argument('-c', '--command', nargs='+', help='detector command')
subtasks_p.add_argument('-f', '--file', help='detector file')
subtasks_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
subtasks_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command')
subtasks_p.add_argument('-vf', '--validator-file', help='validator file')

@set_handler(subtasks_p)
def kg_subtasks(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    # build detector
    validator = None
    detector = Program.from_args(args.file, args.command)
    if not detector: # try validator
        validator = Program.from_args(args.validator_file, args.validator_command)
        detector = detector_from_validator(validator)
        assert (not detector) == (not validator)
    # try detector from details
    if not detector: detector = details.subtask_detector
    # can't build any detector!
    if not detector: raise CommandException("Missing detector/validator")
    # find subtask list
    subtasks = args.subtasks or list(map(str, details.valid_subtasks))

    if validator and not subtasks: # subtask list required for detectors from validator
        raise CommandException("Missing subtask list")

    get_subtasks(subtasks, detector, format_)

def get_subtasks(subtasks, detector, format_, relpath=None):
    subtset = set(subtasks)

    # iterate through inputs, run our detector against them
    subtasks_of = {}
    all_subtasks = set()
    detector.do_compile()
    inputs = []
    for input_ in format_.thru_inputs():
        inputs.append(input_)
        with open(input_) as f:
            result = detector.do_run(*subtasks, stdin=f, stdout=PIPE)
        subtasks_of[input_] = set(result.stdout.decode('utf-8').split())
        if not subtasks_of[input_]:
            raise CommandException("No subtasks found for {}".format(input_))
        if subtset and not (subtasks_of[input_] <= subtset):
            raise CommandException("Found invalid subtasks! {}".format(' '.join(sorted(subtasks_of[input_] - subtset))))

        all_subtasks |= subtasks_of[input_]
        print("Subtasks found for {}: {}".format(input_, ' '.join(sorted(subtasks_of[input_]))))

    print("Distinct subtasks found: {}".format(' '.join(sorted(all_subtasks))))

    if subtset:
        assert all_subtasks <= subtset
        if all_subtasks != subtset:
            print('Warning: Some subtasks not found: {}'.format(' '.join(sorted(subtset - all_subtasks))), file=stderr)

    return subtasks_of, all_subtasks, inputs





##########################################
# generate output data

gen_p = subparsers.add_parser('gen', help='generate output files for some given input files.')

gen_p.add_argument('-F', '--format', '--fmt', help='format of data')
gen_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
gen_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
gen_p.add_argument('-i', '--input', help='input file pattern')
gen_p.add_argument('-o', '--output', help='output file pattern')
gen_p.add_argument('-c', '--command', nargs='+', help='solution command')
gen_p.add_argument('-f', '--file', help='solution file')
gen_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
gen_p.add_argument('-jf', '--judge-file', help='judge file')

@set_handler(gen_p)
def kg_gen(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i', write='o')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    solution = Program.from_args(args.file, args.command) or details.judge_data_maker
    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker

    generate_outputs(format_, solution, judge, details.model_solution)

def generate_outputs(format_, data_maker, judge, model_solution):
    if not data_maker: raise CommandException("Missing solution")
    if not judge: raise CommandException("Missing judge")
    data_maker.do_compile()
    judge.do_compile()
    for input_, output_ in format_.thru_io():
        touch_container(output_)
        with open(input_) as inp:
            with open(output_, 'w') as outp:
                print('WRITING', input_, '-->', output_)
                try:
                    data_maker.do_run(stdin=inp, stdout=outp, time=True)
                except CalledProcessError as cpe:
                    print("The data_maker raised an error for {}".format(input_), file=stderr)
                    exit(cpe.returncode)

        # check with judge if they are the same
        if model_solution == data_maker:
            try:
                judge.do_run(input_, output_, output_)
            except CalledProcessError as cpe:
                print("The judge did not accept {}".format(output_), file=stderr)
                exit(cpe.returncode)





##########################################
# generate output data

test_p = subparsers.add_parser('test', help='test a program against given input and output files.')

test_p.add_argument('-F', '--format', '--fmt', help='format of data')
test_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
test_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
test_p.add_argument('-i', '--input', help='input file pattern')
test_p.add_argument('-o', '--output', help='output file pattern')
test_p.add_argument('-c', '--command', nargs='+', help='solution command')
test_p.add_argument('-f', '--file', help='solution file')
test_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
test_p.add_argument('-jf', '--judge-file', help='judge file')
test_p.add_argument('-js', '--judge-strict', action='store_true', help=argparse.SUPPRESS)# help="whether the checker is a bit too strict and doesn't work if extra arguments are given to it")
test_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
test_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command, for subtask grading')
test_p.add_argument('-vf', '--validator-file', help='validator file, for subtask grading')

@set_handler(test_p)
def kg_test(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='io')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    solution = Program.from_args(args.file, args.command) or details.model_solution
    if not solution: raise CommandException("Missing solution")

    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker
    if not judge: raise CommandException("Missing judge")

    solution.do_compile()
    judge.do_compile()
    total = corrects = 0
    scoresheet = []
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
        print(str(index).rjust(3), 'correct' if correct else 'WRONG' + '!'*11)
        scoresheet.append((index, input_, correct))

    print()
    print('.'*42)
    print('{} out of {} correct'.format(corrects, total))
    print('.'*42)
    print()

    # also print subtask grades

    if details.valid_subtasks:
        validator = Program.from_args(args.validator_file, args.validator_command)
        detector = None
        if validator:
            detector = detector_from_validator(validator)
            assert detector
            print("Found a validator.", end=' ')
        elif details.subtask_detector:
            print("Found a detector in {}.".format(details.source), end=' ')
            detector = details.subtask_detector
        if detector:
            print('Proceeding with subtask grading...')
            # find subtask list
            subtasks = args.subtasks or list(map(str, details.valid_subtasks))
            if validator and not subtasks: # subtask list required for detectors from validator
                raise CommandException("Missing subtask list (for subtask grading)")
            subtasks_of, all_subtasks, inputs = get_subtasks(subtasks, detector, format_)
            # normal grading
            min_score = {sub: 1 for sub in all_subtasks}
            for index, input_, correct in scoresheet:
                for sub in subtasks_of[input_]:
                    min_score[sub] = min(min_score[sub], correct)

            print()
            print('.'*42)
            print('SUBTASK REPORT:')
            for sub in natsorted(all_subtasks):
                print("Subtask {}: Score = {:.3f}".format(str(sub).rjust(3), float(min_score[sub])))





##########################################
# just run the solution

run_p = subparsers.add_parser('run', help='run a program against a set of input files, and print the result to stdout.')

run_p.add_argument('-F', '--format', '--fmt', help='format of data')
run_p.add_argument('-l', '--loc', default='.', help='location of files/package (if format is given)')
run_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
run_p.add_argument('-i', '--input', help='input file pattern')
run_p.add_argument('-o', '--output', help='output file pattern')
run_p.add_argument('-c', '--command', nargs='+', help='solution command')
run_p.add_argument('-f', '--file', help='solution file')

@set_handler(run_p, stderr)
def kg_run(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    solution = Program.from_args(args.file, args.command) or details.judge_data_maker
    if not solution: raise CommandException("Missing solution")

    solution.do_compile()
    for input_ in format_.thru_inputs():
        with open(input_) as inp:
            print('RUNNING FOR', input_, file=stderr)
            try:
                solution.do_run(stdin=inp, time=True)
            except CalledProcessError:
                print('The solution issued a runtime error...', file=stderr)





##########################################
# make everything !!!

make_p = subparsers.add_parser('make', help='create all test data and validate.')

make_p.add_argument('makes', nargs='+', help='what to make. (all, inputs, etc.)')
make_p.add_argument('-l', '--loc', default='.', help='location of files/package')
make_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
make_p.add_argument('--validation', action='store_true', help="Validate the input files against the validators")
make_p.add_argument('--checks', action='store_true', help="Check the output file against the checker")

@set_handler(make_p)
def _kg_make(format_, args):
    if not is_same_format(format_, 'kg'):
        raise CommandException("You can't use '{}' format to 'make'.".format(format_))

    details = Details.from_format_loc(format_, args.details, relpath=args.loc)
    kg_make(args.makes, args.loc, format_, details, validation=args.validation, checks=args.checks)

def kg_make(omakes, loc, format_, details, validation=False, checks=False):
    makes = set(omakes)
    valid_makes = {'all', 'inputs', 'outputs', 'subtasks'}
    if not (makes <= valid_makes):
        raise CommandException("Unknown make param(s): {}".format(' '.join(sorted(makes - valid_makes))))

    if 'all' in makes:
        makes |= valid_makes
        validation = checks = True

    if 'inputs' in makes:
        print()
        print('~~ '*14)
        print('MAKING INPUTS...' + ("WITH VALIDATION..." if validation else 'WITHOUT VALIDATION'))
        if not details.testscript:
            raise CommandException("Missing testscript")

        with open(details.testscript) as scrf:
            script = scrf.read()

        fmt = get_format_from_type(format_, loc, write='i')

        if validation:
            validator = details.validator
            validator.do_compile()

        for filename in run_testscript(fmt.thru_expected_inputs(), script, details.generators, relpath=loc):
            if validation:
                with open(filename) as file:
                    validator.do_run(stdin=file)

        print('DONE MAKING INPUTS.')

    if 'outputs' in makes:
        print()
        print('~~ '*14)
        print('MAKING OUTPUTS...' + ("WITH CHECKER..." if checks else 'WITHOUT CHECKER'))
        fmt = get_format_from_type(format_, loc, read='i', write='o')
        generate_outputs(fmt, details.judge_data_maker, details.checker if checks else Program.noop(), details.model_solution)

        print('DONE MAKING OUTPUTS.')

    if 'subtasks' in makes:
        print()
        print('~~ '*14)
        print('MAKING SUBTASKS...')
        if not details.valid_subtasks:
            if 'subtasks' in omakes:
                raise Exception("valid_subtasks list required if you wish to make subtasks")
            else:
                print("no valid_subtasks found, so actually, subtasks will not be made. move along.")
        else:
            subjson = details.subtasks_files
            if not subjson:
                raise CommandException("A 'subtasks_files' entry in {} is required at this step.".format(details.source))

            detector = details.subtask_detector
            if not detector: raise CommandException("Missing detector/validator")

            # find subtask list
            subtasks = list(map(str, details.valid_subtasks))
            if details.validator and not subtasks: # subtask list required for detectors from validator
                raise CommandException("Missing subtask list")

            # iterate through inputs, run our detector against them
            subtasks_of, all_subtasks, inputs = get_subtasks(subtasks, detector, get_format_from_type(format_, loc, read='i'), relpath=loc)

            print('WRITING TO {}'.format(subjson))
            with open(subjson, 'w') as f:
                f.write('[\n' + '\n'.join('    {},'.format(str(list(x))) for x in construct_subs_files(subtasks_of, inputs)).rstrip(',') + '\n]')

            print('DONE MAKING SUBTASKS.')


def construct_subs_files(subtasks_of, inputs):
    prev, lf, rg = None, 0, -1
    for idx, file in enumerate(inputs):
        assert rg == idx - 1
        subs = subtasks_of[file]
        assert subs
        if prev != subs:
            if prev: yield lf, rg, list(sorted(map(int, prev)))
            prev, lf = subs, idx
        rg = idx
    if prev: yield lf, rg, list(sorted(map(int, prev)))





##########################################
q_p = subparsers.add_parser('joke', help='Print a non-funny joke.')
qs = [
    '10kg > 1kg > 100g > 10g > log > log log > sqrt log log > 1',
    'Spacewaker',
    # add your jokes here plz
]
@set_handler(q_p)
def kg_q(format_, args):
    import random; print(random.choice(qs))





##########################################
# make a new problem

init_p = subparsers.add_parser('init', help='create a new problem, formatted kg-style')

init_p.add_argument('problemcode', help='what to init. (all, inputs, etc.)')
init_p.add_argument('-l', '--loc', default='.', help='where to make the problem')

valid_problemcode = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$')

@set_handler(init_p)
def kg_init(format_, args):
    if not is_same_format(format_, 'kg'):
        raise CommandException("You can't use '{}' format to 'init'.".format(format_))
  
    prob = args.problemcode

    if not valid_problemcode.match(prob):
        raise CommandException("No special characters allowed for the problem code, and the first and last characters must be a letter or a digit.")

    src = os.path.join(script_path, 'data', 'template')
    dest = os.path.join(args.loc, prob)

    print('The destination folder will be', dest)
    if os.path.exists(dest):
        raise CommandException("The folder already exists!")

    env = {
        'problemtitle': ' '.join(re.split(r'[-_. ]+', prob)).title().strip(),
    }

    fmt = Format(os.path.join(src, '*'), os.path.join(dest, '*'), read='i', write='o')
    for inp, outp in fmt.thru_io():
        if not os.path.isfile(inp): continue
        touch_container(outp)
        with open(inp) as inpf:
            with open(outp, 'w') as outpf:
                d = inpf.read()
                if inp.endswith('details.json'): d %= env # so that we can write the title in the json.
                outpf.write(d)

    print('DONE!')





##########################################
# compile source codes for upload

compile_p = subparsers.add_parser('kompile', aliases=['compile'], help='preprocess python source codes to be ready to upload')
compile_p.add_argument('-l', '--loc', default='.', help='location of files/package')
compile_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
compile_p.add_argument('-S', '--shift-left', action='store_true', help=
                                'compress the program by reducing the indentation size from 4 spaces to 1 tab. '
                                'Use at your own risk. (4 is hardcoded because it is the indentation level of the "kg" module.')
compile_p.add_argument('-C', '--compress', action='store_true', help='compress the program by actually compressing it. Use at your own risk.')
# TODO add option for format to "compile" to. No need for now since there are only a few,
#      but later on this will eat up a lot of memory otherwise.

@set_handler(compile_p)
def _kg_compile(format_, args):
    if args.main_command == 'compile':
        print("You spelled 'kompile' incorrectly. I'll let it slide for now.", file=stderr)

    kg_compile(
        format_,
        Details.from_format_loc(format_, args.details),
        'hr', 'pg', 'pc2',
        loc=args.loc,
        shift_left=args.shift_left,
        compress=args.compress,
        )

def kg_compile(format_, details, *target_formats, loc='.', shift_left=False, compress=False):
    if not is_same_format(format_, 'kg'):
        raise CommandException("You can't use '{}' format to 'kompile'.".format(format_))

    # TODO clear kgkompiled first, or at least the target directory

    # locate all necessary files

    # kg libs
    locations = {}
    for kg_lib in 'generators validators checkers utils'.split():
        locations['kg.' + kg_lib] = os.path.join(script_path, kg_lib + '.py')
    kg_libs = set(locations)

    # current files
    all_local = [details.validator, details.checker, details.model_solution] + details.generators + details.other_programs

    @memoize
    def get_module(filename):
        if filename and os.path.isfile(filename) and filename.endswith('.py'):
            module, ext = os.path.splitext(os.path.basename(filename))
            assert ext == '.py'
            return module

    # keep only python files
    all_local = [p for p in all_local if p and get_module(p.filename)]
    for p in all_local:
        locations[get_module(p.filename)] = p.filename

    @memoize
    @listify
    def load_module(module_id):
        if module_id not in locations:
            raise CommandException("Couldn't find module {}! (Add it to other_programs?)".format(module_id))
        with open(locations[module_id]) as f:
            for line in f:
                if not line.endswith('\n'):
                    print('Warning:', locations[module_id], "doesn't end with a new line")
                yield line.rstrip('\n')

    def get_module_id(module, context):
        nmodule = module
        if nmodule.startswith('.'):
            if context['module_id'] in kg_libs:
                nmodule = 'kg' + nmodule

        if nmodule.startswith('.'):
            print("Warning: Ignoring relative import for {}".format(module), file=stderr)
            nmodule = nmodule.lstrip('.')

        return nmodule

    # get subtasks files
    subjson = details.subtasks_files
    subtasks_files = []
    if subjson:
        with open(subjson) as f:
            subtasks_files = json.load(f)

    # convert to various formats
    for fmt, name, copy_files, to_translate in [
            ('pg', 'Polygon', False, [details.validator, details.checker] + details.generators),
            ('hr', 'HackerRank', True, [details.checker]),
            ('pc2', 'PC2', False, [details.validator, details.checker]),
        ]:
        if fmt not in target_formats: continue
        print()
        print('.. '*14)
        print('Compiling for {} ({})'.format(fmt, name))
        dest_folder = os.path.join(loc, 'kgkompiled', fmt)
        to_translate = {g.filename for g in to_translate if g and get_module(g.filename)}
        targets = {}
        found_targets = {}
        for filename in to_translate:
            module = get_module(filename)
            target = os.path.join(dest_folder, os.path.basename(filename))
            targets[module] = target
            if target in found_targets:
                print("Warning: Files have the same destination file ({}): {} and {}".format(target, found_targets[targets], filename), file=stderr)
            found_targets[target] = filename

        for filename in natsorted(to_translate):
            module = get_module(filename)
            print('[{}] converting {} to {}'.format(module, filename, targets[module]))
            touch_container(targets[module])
            lines = list(compile_lines(load_module(module),
                    module_id=module,
                    module_file=filename,
                    load_module=load_module,
                    get_module_id=get_module_id,
                    format=fmt,
                    details=details,
                    subtasks_files=subtasks_files,
                    snippet=False,
                    subtasks_only=False,
                    shift_left=shift_left,
                    compress=compress,
                ))
            with open(targets[module], 'w') as f:
                shebanged = False
                for line in lines:
                    assert not line.endswith('\n')
                    if not shebanged and not line.startswith('#!'):
                        shebang_line = "#!/usr/bin/env python3"
                        print('adding shebang line {}'.format(repr(shebang_line)))
                        print(shebang_line, file=f)
                    shebanged = True
                    print(line, file=f)

        # TODO for hackerrank, check that the last file for each subtask is unique to that subtask.

        if fmt == 'hr' and details.checker and get_module(details.checker.filename): # snippets for hackerrank upload.
            # pastable version of grader
            filename = details.checker.filename
            module = get_module(filename)

            target = os.path.join(dest_folder, 'hr.pastable.version.' + os.path.basename(filename))
            print('[{}] writing snippet version of {} to {}'.format(module, filename, target))
            touch_container(target)
            lines = list(compile_lines(load_module(module),
                    module_id=module,
                    module_file=filename,
                    load_module=load_module,
                    get_module_id=get_module_id,
                    format=fmt,
                    details=details,
                    subtasks_files=subtasks_files,
                    snippet=True,
                    subtasks_only=False,
                    shift_left=shift_left,
                    compress=compress,
                ))
            with open(target, 'w') as f:
                print("# NOTE: THIS SCRIPT IS MEANT TO BE PASTED TO HACKERRANK'S CUSTOM CHECKER, NOT RUN ON ITS OWN.", file=f)
                for line in lines:
                    assert not line.endswith('\n')
                    print(line, file=f)

            target = os.path.join(dest_folder, 'hr.subtasks.only.' + os.path.basename(filename))
            print('[{}] writing the subtasks snippet of {} to {}'.format(module, filename, target))
            touch_container(target)
            lines = list(compile_lines(load_module(module),
                    module_id=module,
                    module_file=filename,
                    load_module=load_module,
                    get_module_id=get_module_id,
                    format=fmt,
                    details=details,
                    subtasks_files=subtasks_files,
                    snippet=True,
                    subtasks_only=True,
                    write=False,
                ))
            with open(target, 'w') as f:
                print('# NOTE: THIS SCRIPT IS NOT MEANT TO BE RUN ON ITS OWN.', file=f)
                for line in lines:
                    assert not line.endswith('\n')
                    print(line, file=f)


        # copy over the files
        if copy_files:
            print('copying test data from', loc, 'to', dest_folder, '...')
            convert_formats(
                    (format_, loc),
                    (fmt, dest_folder),
                )

        if fmt == 'hr':
            zipname = os.path.join(dest_folder, 'upload_this_to_hackerrank.zip')
            print('making zip for HackerRank...', zipname)
            def get_arcname(filename):
                assert os.path.samefile(dest_folder, os.path.commonpath([dest_folder, filename]))
                return os.path.relpath(filename, start=dest_folder)
            with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for inp, outp in HRFormat(dest_folder, read='io').thru_io():
                    for fl in inp, outp:
                        zipf.write(fl, arcname=get_arcname(fl))

        print('Done for {} ({})'.format(fmt, name))

    print('.. '*14)




##########################################
# compile a contest from a configuration file

contest_p = subparsers.add_parser('kontest', aliases=['contest'], help='Compile a contest')
contest_p.add_argument('format', help='Contest format to compile to')
contest_p.add_argument('config', help='JSON file containing the contest configuration')
contest_p.add_argument('-m', '--make-all', action='store_true', help='Run "kg make all" in all problems')
contest_p.add_argument('-ns', '--no-seating', action='store_true', help='Skip the creation of the seating arrangement')
contest_p.add_argument('-s', '--seed', type=int, help='Initial seed to use')

def problem_letters():
    for l in count(1):
        for c in ascii_uppercase:
            yield l * c

@set_handler(contest_p)
def kg_contest(format_, args):
    if args.main_command == 'contest':
        print("You spelled 'kontest' incorrectly. I'll let it slide for now.", file=stderr)

    if not is_same_format(format_, 'kg'):
        raise CommandException("You can't use '{}' format to 'kontest'.".format(format_))

    if args.format != 'pc2':
        raise CommandException("Unsupported contest format: {}".format(args.format))

    # TODO possibly use a yaml library here, but for now this will do.
    # It might be a hassle to add another dependency.
    contest = ContestDetails.from_loc(args.config)

    seedval = args.seed
    if seedval is None: seedval = randrange(10**6)

    if args.format == 'pc2':

        # identify key folders
        contest_folder = os.path.join('kgkompiled', contest.code)
        cdp_config = os.path.join(contest_folder, 'CDP', 'config')
        ext_data = os.path.join(contest_folder, 'ALLDATA')
        contest_template = os.path.join(script_path, 'data', 'contest_template', 'pc2')

        # construct template environment
        if not contest.site_password: raise CommandException("site_password required for PC2")
        env = {
            "datetime_created": datetime.now(),
            "title": contest.title,
            "code": contest.code,
            "duration": contest.duration,
            "scoreboard_freeze_length": contest.scoreboard_freeze_length,
            "site_password": contest.site_password,
            "team_count": len(contest.teams),
            "judge_count": len(contest.judges),
            "admin_count": len(contest.admins),
            "leaderboard_count": len(contest.leaderboards),
            "feeder_count": len(contest.feeders),
            "filename": "{:mainfile}",
            "filename_base": "{:basename}",
            "alldata": os.path.abspath(ext_data),
        }

        # problem envs
        found_codes = {}
        problem_env = {}
        letters = []
        for letter, problem_loc in zip(problem_letters(), contest.problems):
            details = Details.from_format_loc(format_, os.path.join(problem_loc, 'details.json'), relpath=problem_loc)

            code = os.path.basename(problem_loc)
            if code in found_codes:
                found_codes[code] += 1
                code += str(found_codes[code])
            else:
                found_codes[code] = 1
            print()
            print('-'*42)
            print("Getting problem {} (from {})".format(repr(code), problem_loc))

            if args.make_all:
                print('Running "kg make all"...')
                kg_make(['all'], problem_loc, format_, details)

            time_limit = int(round(details.time_limit))
            if time_limit != details.time_limit:
                raise ValueError("The time limit must be an integer for PC2: {} {}".format(problem_loc, time_limit))

            letters.append(letter)
            problem_env[letter] = {
                'problem_loc': problem_loc,
                'details': details,
                'letter': letter,
                'problem_code': code,
                'title': details.title,
                'letter_title': '{}: {}'.format(letter, details.title),
                'time_limit': time_limit,
            }

            # put validator in input_validators/, and checker to output_validators/
            kg_compile(format_, details, 'pc2', loc=problem_loc)
            for name, targ in [
                    ('validator', 'input_validators'),
                    ('checker', 'output_validators'),
                ]:
                src = getattr(details, name)
                srcf = os.path.join(problem_loc, 'kgkompiled', 'pc2', os.path.basename(src.filename))
                targf = os.path.join(cdp_config, code, targ, os.path.basename(src.filename))
                touch_container(targf)
                copyfile(srcf, targf)
                problem_env[letter][name] = os.path.abspath(targf)

        def yaml_lang(lang):
            with open(os.path.join(contest_template, '1language.yaml')) as f:
                lenv = {key: (
                    value.format(**env) if isinstance(value, str) else
                    str(value).lower() if isinstance(value, bool) else value) for key, value in lang.items()}
                run = lenv['run'] + ' '
                spacei = run.index(' ')
                lenv.update({
                        "run_first": run[:spacei],
                        "run_rest": run[spacei+1:-1]
                    })
                return f.read().format(**lenv)

        def yaml_problem(letter):
            with open(os.path.join(contest_template, '1problem.yaml')) as f:
                return f.read().format(**problem_env[letter])

        env['yaml_langs'] = '\n'.join(map(yaml_lang, contest.langs))
        env['yaml_problems'] = '\n'.join(map(yaml_problem, letters))

        print()
        print('-'*42)
        print('Writing contest config files')
        for file in ['contest.yaml', 'problemset.yaml']:
            print('Writing', file)
            source = os.path.join(contest_template, file)
            target = os.path.join(cdp_config, file)
            touch_container(target)
            with open(source) as source_f:
                with open(target, 'w') as target_f:
                    target_f.write(source_f.read().format(**env))

        print()
        print('-'*42)
        print('Writing problem files')
        for letter in letters:
            penv = dict(env)
            penv.update(problem_env[letter])
            code = penv['problem_code']
            for file in ['problem.yaml', os.path.join('problem_statement', 'problem.tex')]:
                print('Writing', file, 'for', code)
                source = os.path.join(contest_template, os.path.basename(file))
                target = os.path.join(cdp_config, code, file)
                touch_container(target)
                with open(source) as source_f:
                    with open(target, 'w') as target_f:
                        target_f.write(source_f.read().format(**penv))

            print("Copying model solution")
            source = penv['details'].model_solution.filename
            target = os.path.join(cdp_config, code, 'submissions', 'accepted', os.path.basename(source))
            touch_container(target)

            copyfile(source, target)

            print("Copying data for {}...".format(code))
            try:
                src_format = KGFormat(penv['problem_loc'], read='io')
            except FormatException as exc:
                raise CommandException("No tests found for '{}'. Please run 'kg make all' to generate the files, or call 'kg kontest' with the '-m' option.".format(penv['problem_loc'])) from exc
            for data_loc in [
                    os.path.join(cdp_config, code, 'data', 'secret'),
                    os.path.join(ext_data, code),
                ]:
                print("Copying to", data_loc)
                dest_format = KGFormat(write='io', tests_folder=data_loc)
                copied = 0
                for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
                    touch_container(dsti)
                    touch_container(dsto)
                    copyfile(srci, dsti)
                    copyfile(srco, dsto)
                    copied += 2
                print("Copied", copied, "files")

    print()
    print('-'*42)
    print('Making passwords')
    write_passwords_format(contest, args.format, seedval=seedval, dest=contest_folder)

    if not args.no_seating and contest.seating:
        print()
        print('-'*42)
        print('Writing seating arrangement')
        write_seating(contest, seedval=seedval, dest=contest_folder)





##########################################
# manage seating arrangements

seating_args(subparsers.add_parser('seating', help='Manage seating arrangements'))





##########################################
# Generate passwords

passwords_p = subparsers.add_parser('passwords', help='Assign passwords to a list of teams')
passwords_p.add_argument('teams', help='JSON file containing the team and school details')
passwords_p.add_argument('-s', '--seed', type=int, help='Initial seed to use')
passwords_p.add_argument('-c', '--code', '--contest-code', help='Contest code')
passwords_p.add_argument('-t', '--title', '--contest-title', help='Contest title')
passwords_p.add_argument('-a', '--account-format', default='team{idx}', help='Account name format')

@set_handler(passwords_p)
def kg_passwords(format_, args):
    with open(args.teams) as f: team_schools = ContestDetails.get_team_schools(json.load(f))

    team_names = [team for ts in team_schools for team in ts['teams']]
    passwords, seed = create_passwords(team_names, seedval=args.seed)

    def get_team_schools():
        for ts in team_schools:
            for idx, team in enumerate(ts['teams'], 1):
                yield ts['school'], team, idx

    def get_accounts():
        for idx, (school_name, team_name, school_idx) in enumerate(get_team_schools(), 1):
            account = args.account_format.format(
                    idx=idx,
                    school_idx=school_idx,
                    school_name=school_name,
                    team_name=team_name,
                    first1=team_name.split()[0][0],
                    first=team_name.split()[0],
                    last1=team_name.split()[-1][0],
                    last=team_name.split()[-1],
                )
            yield school_name, team_name, account, passwords[team_name]

    write_passwords(list(get_accounts()), 'kgkompiled', seedval=' or '.join({str(x) for x in [args.seed, seed] if x is not None}), code=args.code, title=args.title)





##########################################
def main(format='kg'):
    args = parser.parse_args()
    logf = args.default_file
    print('\n' + '='*42 + '\n', file=logf)
    args.handler(format, args)
    print('\n' + '='*42 + '\n', file=logf)
    print('THE COMMAND FINISHED SUCCESSFULLY.', file=logf)
