from collections import defaultdict, OrderedDict
from datetime import datetime
from functools import wraps
from html.parser import HTMLParser
from operator import attrgetter
from random import randrange, shuffle
from shutil import rmtree, make_archive
from string import ascii_letters, ascii_uppercase, digits
from subprocess import PIPE, CalledProcessError, SubprocessError, TimeoutExpired
from sys import stdin, stdout, stderr
from textwrap import dedent
import argparse
import contextlib
import os.path
import re
import tempfile
import yaml
import zipfile

from argcomplete import autocomplete
from jinja2 import Template
from natsort import natsorted

from ..black_magic import *
from .contest_details import *
from .details import *
from .formats import *
from .passwords import *
from .programs import *
from .seating import *
from .testscripts import *
from .utils import *


class CommandError(Exception): ...

VERSION = "0.2"




##########################################

# TODO use the 'logging' library

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=cformat_text(dedent('''\
                Programming contest utilities.

                Two main use cases are the following:

                - For one-off scripting tasks, e.g., testing a solution against a bunch of data.

                    - (for problems) [*[kg gen]*], [*[kg test]*], [*[kg run]*], [*[kg subtasks]*], [*[kg compile]*]
                    - (for contests) [*[kg seating]*], [*[kg passwords]*]
                    - (others) [*[kg convert]*], [*[kg convert-sequence]*]

                - For developing problems/contests from scratch (writing generators, validators, checkers, etc.)

                    - (for problems) [*[kg init]*], [*[kg make]*], [*[kg gen]*]/[*[test]*]/[*[run]*]/[*[kg compile]*]
                    - (for contests) [*[kg contest]*]

                See the individual --help texts for each command, e.g., [*[kg init --help]*].
        ''')))
parser.add_argument('--krazy', action='store_true', help="Go krazy. (Don't use unless drunk)")
# TODO add 'verbose' option here
subparsers = parser.add_subparsers(help='which operation to perform', dest='main_command')
subparsers.required = True





##########################################
# convert one format to another

convert_p = subparsers.add_parser('konvert',
            aliases=['convert'],
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Convert test data from one format to another',
        description=cformat_text(dedent('''\
                Convert test data from one contest/judge system format to another.


                $ [*[kg convert --from [src_fmt] [src_folder] --to [dest_fmt] [dest_folder]]*]


                For example,

                $ [*[kg convert --from polygon path/to/polygon-package --to hackerrank path/to/hr/i-o-folders]*]
                $ [*[kg convert --from hackerrank path/to/hr/i-o-folders --to polygon path/to/polygon-package]*]

                'polygon' and 'hackerrank' can be abbreviated as 'pg' and 'hr', respectively. There is also the
                'kompgen'/'kg' format, which is the format used when creating a problem from scratch using KompGen.


                A few details on the "formats":

                -    Polygon I/O pairs look like:  tests/*           and  tests/*.a
                - HackerRank I/O pairs look like:  input/input*.txt  and  output/output*.txt
                -    KompGen I/O pairs look like:  tests/*.in        and  tests/*.ans

                You can think of "kg convert" as similar to two calls to "kg convert-sequence", one for the input
                files, and another for the output files, with some additional validity checks (e.g., for HackerRank,
                input/inputFOO.txt is rejected) and reindexing (e.g., Polygon starts at "1", e.g., tests/1, but
                HackerRank starts at "00", e.g., input/input00.txt).
        ''')))
convert_p.add_argument('--from', nargs=2, help='source format and location', dest='fr',
                                 metavar=('FROM_FORMAT', 'FROM_FOLDER'), required=True)
convert_p.add_argument('--to',   nargs=2, help='destination format and location',
                                 metavar=('TO_FORMAT', 'TO_FOLDER'), required=True)

@set_handler(convert_p)
def kg_convert(format_, args):
    if args.main_command == 'convert':
        info_print("You spelled 'konvert' incorrectly. I'll let it slide for now.", file=stderr)
    
    convert_formats(args.fr, args.to)

def convert_formats(src, dest, *, src_kwargs={}, dest_kwargs={}):
    sformat, sloc = src
    dformat, dloc = dest
    src_format = get_format(argparse.Namespace(format=sformat, loc=sloc, input=None, output=None), read='io', **src_kwargs)
    dest_format = get_format(argparse.Namespace(format=dformat, loc=dloc, input=None, output=None), write='io', **dest_kwargs)

    copied = 0
    info_print("Copying now...")
    for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
        copy_file(srci, dsti)
        copy_file(srco, dsto)
        copied += 2
    succ_print("Copied", copied, "files")





##########################################
# convert one file sequence to another

convert2_p = subparsers.add_parser('konvert-sequence',
            aliases=['convert-sequence'],
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Convert a file sequence with a certain pattern to another',
        description=cformat_text(dedent('''\
                Convert a file sequence with a certain pattern to another.


                $ [*[kg convert-sequence --from [source_pattern] --to [target_pattern]]*]

                This converts every file matched by [source_pattern] into a file that matches [target_pattern].

                The output files will be inferred from the corresponding input files. "*" in patterns are
                wildcards, and they will be matched automatically.


                For example,

                $ [*[kg convert-sequence --from "input/input*.txt" --to "tests/0*.in"]*]

                will convert input/input00.txt to tests/000.in, input/input11.txt to tests/011.in, etc.

                Quotes are required (at least on Linux), otherwise bash will replace it with the
                actual matched filenames. (not sure about Windows)


                There can even be multiple "*"s in --to and --from. The only requirement is that they have an equal
                number of "*"s. Parts matched by "*"s will be transferred to the corresponding "*" in the other
                pattern.
        ''')))
convert2_p.add_argument('--from', help='source file pattern', dest='fr', required=True)
convert2_p.add_argument('--to', help='destination file pattern', required=True)

@set_handler(convert2_p)
def kg_convert2(format_, args):
    if args.main_command == 'convert-sequence':
        info_print("You spelled 'konvert-sequence' incorrectly. I'll let it slide for now.", file=stderr)

    convert_sequence(args.fr, args.to)

def convert_sequence(src, dest):
    format_ = get_format(argparse.Namespace(format=None, loc=None, input=src, output=dest), read='i', write='o')

    copied = 0
    info_print("Copying now...")
    for srcf, destf in format_.thru_io():
        copy_file(srcf, destf)
        copied += 1
    succ_print("Copied", copied, "files")





##########################################
# detect subtasks

subtasks_p = subparsers.add_parser('subtasks',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Detect the subtasks of input files',
        description=cformat_text(dedent('''\
                Detect the subtasks of input files, for problems with subtasks.

                You need either a detector program or a validator program.


                $ [*[kg subtasks -i [input_pattern] -f [detector_program]]*]

                This prints all subtasks of every file. [detector_program] must be a program that takes an input
                from stdin and prints the distinct subtasks in which it is valid, as separate tokens in stdout.


                $ [*[kg subtasks -i [input_pattern] -vf [validator_program]]*]

                This is a bit slower but simpler. [validator_program] must be a program that takes an input from
                stdin and the subtask name as the first command line argument, and exits with code 0 iff the input
                is valid from that subtask.

                This is useful if you want to automatically know which subtask each file belongs to; sometimes, a
                file you generated may be intended for a subtask but actually violates the constraints, so this lets
                you detect those cases.


                For example,

                $ [*[kg subtasks -i "tests/*.in" -f Detector.java]*]
                $ [*[kg subtasks -i "tests/*.in" -vf validator.cpp]*]

                Quotes are required (at least on Linux), otherwise bash will replace it with the
                actual matched filenames. (not sure about Windows)

                The programming language of the detector/validator is inferred from the extension. You can also pass
                a full command using -c or -vc, for example,

                $ [*[kg subtasks -i "tests/*.in" -c pypy3 detector.py]*]
                $ [*[kg subtasks -i "tests/*.in" -vc runhaskell validator.hs]*]


                You can also run this for just one file, e.g.,

                $ [*[kg subtasks -i data/sample.in -f Detector.java]*]

                There can even be multiple "*"s in -i.


                If you wrote your problem using "kg init", then you may omit "-i", "-f" and "-vf"; they will default
                to the KompGen format ("tests/*.in"), and other details will be parsed from details.json, so
                "[*[kg subtasks]*]" without options would just work. (You can still pass them of course.)


                If your command (-c or -vc) requires leading dashes, then the argument parser might interpret them as
                options to "kg subtasks" itself. To work around this, prepend "___" (triple underscore) to each part
                containing a "-". The "___" will be ignored. For example,

                $ [*[kg subtasks -i "tests/*.in" -vc java ___-Xss128m Validator]*]
        ''')))
subtasks_p.add_argument('-F', '--format', '--fmt', help='format of data')
subtasks_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
subtasks_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
subtasks_p.add_argument('-i', '--input', help='input file pattern')
subtasks_p.add_argument('-o', '--output', help='output file pattern')
subtasks_p.add_argument('-c', '--command', nargs='+', help='detector command')
subtasks_p.add_argument('-f', '--file', help='detector file')
subtasks_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
subtasks_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command')
subtasks_p.add_argument('-vf', '--validator-file', help='validator file')
# TODO support "compiler through validator"

@set_handler(subtasks_p)
def kg_subtasks(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    subtasks = args.subtasks or list(map(str, details.valid_subtasks))
    detector = _get_subtask_detector_from_args(args, purpose='subtask computation', details=details)

    compute_subtasks(subtasks, detector, format=format_)

def _get_subtask_detector_from_args(args, *, purpose, details=None):
    if details is None:
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
    if not detector: raise CommandError(f"Missing detector/validator (for {purpose})")
    # find subtask list

    if validator and not subtasks: # subtask list required for detectors from validator
        raise CommandError(f"Missing subtask list (for {purpose})")

    return detector

def _collect_subtasks(input_subs):
    @wraps(input_subs)
    def _input_subs(subtasks, *args, **kwargs):
        subtset = set(subtasks)

        # iterate through inputs, run our detector against them
        subtasks_of = OrderedDict()
        all_subtasks = set()
        files_of_subtask = {sub: set() for sub in subtset}
        for input_, subs in input_subs(subtasks, *args, **kwargs):
            subtasks_of[input_] = set(subs)
            if not subtasks_of[input_]:
                raise CommandError(f"No subtasks found for {input_}")
            if subtset and not (subtasks_of[input_] <= subtset):
                raise CommandError("Found invalid subtasks! " + ' '.join(map(repr, sorted(subtasks_of[input_] - subtset))))
            all_subtasks |= subtasks_of[input_]
            for sub in subtasks_of[input_]: files_of_subtask[sub].add(input_)
            info_print(f"Subtasks found for {input_}:", end=' ')
            key_print(*sorted(subtasks_of[input_]))

        info_print("Distinct subtasks found:", end=' ')
        key_print(*natsorted(all_subtasks))

        if subtset:
            assert all_subtasks <= subtset
            if all_subtasks != subtset:
                warn_print('Warning: Some subtasks not found:', *natsorted(subtset - all_subtasks), file=stderr)

        info_print("Subtask dependencies:")
        for sub in natsorted(subtset):
            if files_of_subtask[sub]:
                deps = [dep for dep in natsorted(subtset) if dep != sub and files_of_subtask[dep] <= files_of_subtask[sub]]
                print(info_text("Subtask"), key_text(sub), info_text("contains the ff subtasks:"), key_text(*deps))

        return subtasks_of, all_subtasks

    return _input_subs

@_collect_subtasks
def extract_subtasks(subtasks, subtasks_files, *, format=None, inputs=None):
    if not inputs: inputs = []
    thru_expected_inputs = format.thru_expected_inputs() if format else None
    def get_expected_input(i):
        while i >= len(inputs):
            if not thru_expected_inputs: raise CommandError("Missing format or input")
            inputs.append(next(thru_expected_inputs))
        return inputs[i]

    input_ids = set()
    for lf, rg, subs in subtasks_files:
        for index in range(lf, rg + 1):
            if index in input_ids: raise CommandError(f"File {index} appears multiple times in subtasks_files")
            input_ids.add(index)
            yield get_expected_input(index), {*map(str, subs)}

@_collect_subtasks
def compute_subtasks(subtasks, detector, *, format=None, relpath=None):
    subtset = set(subtasks)

    # iterate through inputs, run our detector against them
    detector.do_compile()
    for input_ in format.thru_inputs():
        with open(input_) as f:
            try:
                result = detector.do_run(*subtasks, stdin=f, stdout=PIPE, check=True)
            except CalledProcessError as cpe:
                err_print(f"The detector raised an error for {input_}", file=stderr)
                raise CommandError(f"The detector raised an error for {input_}") from cpe
        yield input_, set(result.stdout.decode('utf-8').split())





##########################################
# generate output data

gen_p = subparsers.add_parser('gen',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Run a program against several files as input, and generate an output file for each',
        description=cformat_text(dedent('''\
                Run a program against several files as input, and generate an output file for each.

                A common use is to generate output data from the input data using the solution program.


                $ [*[kg gen -i [input_pattern] -o [output_pattern] -f [program]]*]

                This generates the files [output_pattern] by running [program] for every file in [input_pattern].
                [program] must be a program that takes an input from stdin and prints the output in stdout.

                The output files will be inferred from the corresponding input files. "*" in patterns are
                wildcards, and they will be matched automatically.


                For example,

                $ [*[kg gen -i "tests/*.in" -o "tests/*.ans" -f Solution.java]*]

                Here, input files "tests/*.in" will be converted to output files "tests/*.ans", with the part in
                the "*" carrying over. For example, "tests/005.in" corresponds to "tests/005.ans".

                Quotes are required (at least on Linux), otherwise bash will replace it with the actual matched
                filenames. (not sure about Windows)

                The programming language of the program is inferred from the extension. You can also pass a full
                command using -c, for example,

                $ [*[kg gen -i "tests/*.in" -o "tests/*.ans" -c pypy3 solution.py]*]


                You can also run this for just one file, e.g.,

                $ [*[kg gen -i data/sample.in -o data/temp.txt -f solution.cpp]*]

                There can even be multiple "*"s in -i and -o. The only requirement is that they have an equal
                number of "*"s. Parts matched by "*"s will be transferred to the corresponding "*" in the other
                pattern.


                If you wrote your problem using "kg init", then you may omit "-i", "-o" and "-f"; they will
                default to the KompGen format ("tests/*.in" and "tests/*.ans"), and other details will be parsed
                from details.json, so for example, "[*[kg gen]*]" without options would just work. (You can still pass
                them of course.)


                If your command (-c) requires leading dashes, then the argument parser might interpret them as
                options to "kg gen" itself. To work around this, prepend "___" (triple underscore) to each part
                containing a "-". The "___" will be ignored. For example,

                $ [*[kg gen -c java ___-Xss128m Solution]*]
        ''')))

gen_p.add_argument('-F', '--format', '--fmt', help='format of data')
gen_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
gen_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
gen_p.add_argument('-i', '--input', help='input file pattern')
gen_p.add_argument('-o', '--output', help='output file pattern')
gen_p.add_argument('-c', '--command', nargs='+', help='solution/data_maker command')
gen_p.add_argument('-f', '--file', help='solution/data_maker file')
gen_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
gen_p.add_argument('-jf', '--judge-file', help='judge file')
# TODO Add "clear matched" option, but explicitly ask if delete them?

@set_handler(gen_p)
def kg_gen(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i', write='o')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    judge_data_maker = Program.from_args(args.file, args.command)
    model_solution = None
    if not judge_data_maker:
        model_solution = details.model_solution
        judge_data_maker = details.judge_data_maker
    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker

    if not judge: raise CommandError("Missing judge")

    generate_outputs(format_, judge_data_maker, model_solution=model_solution,
            judge=judge, interactor=details.interactor)

def generate_outputs(format_, data_maker, *, model_solution=None, judge=None, interactor=None):
    if not data_maker: raise CommandError("Missing solution")
    data_maker.do_compile()
    if judge: judge.do_compile()
    if model_solution and model_solution != data_maker: model_solution.do_compile()
    if interactor: interactor.do_compile()
    data_maker_name = 'model_solution' if model_solution == data_maker else 'data_maker'
    for input_, output_ in format_.thru_io():
        touch_container(output_)
        print(info_text('WRITING', input_, '-->'), key_text(output_))
        try:
            if data_maker.attributes.get('interacts') and interactor:
                results = data_maker.do_interact(interactor, time=True, check=True,
                        interactor_args=[input_, output_],
                        interactor_kwargs=dict(time=True, check=True),
                    )
            else:
                with open(input_) as inp, open(output_, 'w') as outp:
                    data_maker.do_run(stdin=inp, stdout=outp, time=True, check=True)
        except InteractorException as ie:
            err_print(f"The interactor raised an error with the {data_maker_name} for {input_}", file=stderr)
            raise CommandError(f"The interactor raised an error with the {data_maker_name} for {input_}") from ie
        except SubprocessError as se:
            err_print(f"The {data_maker_name} raised an error for {input_}", file=stderr)
            raise CommandError(f"The {data_maker_name} raised an error for {input_}") from se

        if judge and model_solution:
            @contextlib.contextmanager  # so that the file isn't closed
            def model_output():
                if model_solution == data_maker:
                    yield output_
                else:
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        info_print(f"Running model solution on {input_}")
                        try:
                            if interactor:
                                results = model_solution.do_interact(interactor, time=True, check=True,
                                        interactor_args=[input_, tmp.name],
                                        interactor_kwargs=dict(time=True, check=True),
                                    )
                            else:
                                with open(input_) as inp:
                                    model_solution.do_run(stdin=inp, stdout=tmp, time=True, check=True)
                        except InteractorException as ie:
                            err_print(f"The interactor raised an error with the model_solution for {input_}", file=stderr)
                            raise CommandError(f"The interactor raised an error with the model_solution for {input_}") from ie
                        except SubprocessError as se:
                            err_print(f"The interaction raised an error for {input_}", file=stderr)
                            raise CommandError(f"The interaction raised an error for {input_}") from se
                        yield tmp.name
            with model_output() as model_out:
                try:
                    judge.do_run(*map(os.path.abspath, (input_, model_out, output_)), check=True)
                except CalledProcessError as cpe:
                    err_print(f"The judge did not accept {output_}", file=stderr)
                    raise CommandError(f"The judge did not accept {output_}") from cpe





##########################################
# test against output data

test_p = subparsers.add_parser('test',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Test a program against given input and output files',
        description=cformat_text(dedent('''\
                Test a program against given input and output files.

                $ [*[kg gen -i [input_pattern] -o [output_pattern] -f [solution_program]]*]

                This runs [solution_program] for every file in [input_pattern], and compares it against the
                corresponding files in [output_pattern]. [solution_program] must be a program that takes an
                input from stdin and prints the output in stdout.

                The output files will be inferred from the corresponding input files. "*" in patterns are
                wildcards, and they will be matched automatically.


                For example,

                $ [*[kg test -i "tests/*.in" -o "tests/*.ans" -f Solution.java]*]

                Here, input files "tests/*.in" will be matched with output files "tests/*.ans", with the part in
                the "*" carrying over. For example, "tests/005.in" corresponds to "tests/005.ans".

                Quotes are required (at least on Linux), otherwise bash will replace it with the
                actual matched filenames. (not sure about Windows)

                The programming language of the program is inferred from the extension. You can also pass a full
                command using -c, for example,

                $ [*[kg test -i "tests/*.in" -o "tests/*.ans" -c pypy3 solution.py]*]


                You can also run this for just one file, e.g.,

                $ [*[kg test -i data/sample.in -o data/temp.txt -f solution.cpp]*]

                There can even be multiple "*"s in -i and -o. The only requirement is that they have an equal
                number of "*"s. Parts matched by "*"s will be transferred to the corresponding "*" in the other
                pattern.


                If your program has a custom checker file, you may pass it via the -jf ("judge file") option.
                For example,

                $ [*[kg test -i "tests/*.in" -o "tests/*.ans" -f Solution.java -jf checker.py]*]

                Here, checker.py takes three command line arguments "input_path", "output_path" and "judge_path",
                and exits with 0 iff the answer is correct. It may print anything in stdout/stderr.

                You may also pass a full checker command via -jc, similar to -c for the solution file.


                If you wrote your problem using "kg init", then you may omit "-i", "-o", "-f" and "-jf; they will
                default to the KompGen format ("tests/*.in" and "tests/*.ans"), and other details will be parsed
                from details.json, so for example, "[*[kg test]*]" without options would just work. (You can still pass
                them of course.)


                If your command (-c, -jc or -vc) requires leading dashes, then the argument parser might interpret
                them as options to "kg test" itself. To work around this, prepend "___" (triple underscore) to each
                part containing a "-". The "___" will be ignored. For example,

                $ [*[kg test -c java ___-Xss128m Solution -jc java ___-Xss128m Checker]*]
        ''')))

test_p.add_argument('-F', '--format', '--fmt', help='format of data')
test_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
test_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
test_p.add_argument('-i', '--input', help='input file pattern')
test_p.add_argument('-o', '--output', help='output file pattern')
test_p.add_argument('-c', '--command', nargs='+', help='solution command')
test_p.add_argument('-f', '--file', help='solution file')
test_p.add_argument('-jc', '--judge-command', nargs='+', help='judge command')
test_p.add_argument('-jf', '--judge-file', help='judge file')
test_p.add_argument('-js', '--judge-strict-args', action='store_true',
                                                  help="whether the checker is strict and doesn't work if "
                                                       "extra arguments are given to it")
test_p.add_argument('-s', '--subtasks', default=[], nargs='+', help='list of subtasks')
test_p.add_argument('-vc', '--validator-command', nargs='+', help='validator command, for subtask grading')
test_p.add_argument('-vf', '--validator-file', help='validator file, for subtask grading')
test_p.add_argument('-ic', '--interactor-command', nargs='+', help='interactor command, if the problem is interactive')
test_p.add_argument('-if', '--interactor-file', help='interactor file, if the problem is interactive')
test_p.add_argument('-tl', '--time-limit', type=float, help="the problem's time limit (or -1 for no limit); "
                                                            "the code will be terminated if it exceeds 4x this time")

@set_handler(test_p)
def kg_test(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='io')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    solution = Program.from_args(args.file, args.command) or details.model_solution
    if not solution: raise CommandError("Missing solution")

    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker
    if not judge: raise CommandError("Missing judge")

    interactor = Program.from_args(args.interactor_file, args.interactor_command) or details.interactor

    time_limit = args.time_limit
    if time_limit is None: time_limit = details.time_limit
    if time_limit == -1: time_limit = float('inf')
    print(info_text('Using problem time limit:'), key_text(time_limit), info_text('sec.'))

    judge_strict_args = args.judge_strict_args
    solution.do_compile()
    judge.do_compile()
    if interactor: interactor.do_compile()
    total = corrects = 0
    scoresheet = []
    max_time = 0
    for index, (input_, output_) in enumerate(format_.thru_io()):
        def get_score():
            nonlocal max_time, judge_strict_args
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                with tempfile.NamedTemporaryFile(delete=False) as result_tmp:
                    info_print("\nFile", str(index).rjust(3), 'CHECKING AGAINST', input_)
                    try:
                        if interactor:
                            solution_res, interactor_res = solution.do_interact(interactor,
                                    time=True, check=True,
                                    interactor_args=(input_, tmp.name),
                                    interactor_kwargs=dict(check=False),
                                    time_limit=time_limit,
                                )
                        else:
                            interactor_res = None
                            with open(input_) as inp:
                                solution_res = solution.do_run(
                                        stdin=inp,
                                        stdout=tmp,
                                        time=True,
                                        check=True,
                                        time_limit=time_limit,
                                    )
                    except TimeoutExpired:
                        pass
                    except CalledProcessError:
                        err_print('The solution issued a runtime error...')
                        return False, 0.0
                    finally:
                        # save the running time now, since we're monkeying around...
                        running_time = solution.last_running_time
                        max_time = max(max_time, running_time)

                    # Check if the interactor issues WA by itself. Don't invoke the judge
                    if getattr(interactor_res, 'returncode', 0):
                        err_print('The interactor did not accept the interaction...')
                        return False, 0.0

                    def run_judge():
                        jargs = list(map(os.path.abspath, (input_, tmp.name, output_)))
                        if not judge_strict_args:
                            jargs += [result_tmp.name, '-c', solution.filename, '-t', str(index), '-v']
                        return judge.do_run(*jargs, check=False).returncode

                    info_print("Checking the output...")
                    returncode = run_judge()
                    if returncode == 3 and not judge_strict_args: # try again but assume the judge is strict
                        info_print("The error above might just be because of testlib... trying to judge again")
                        judge_strict_args = True
                        returncode = run_judge()
                    correct = returncode == 0

                    try:
                        with open(result_tmp.name) as result_tmp_file:
                            score = json.load(result_tmp_file)['score']
                    except Exception as exc:
                        score = 1.0 if correct else 0.0 # can't read score. use binary scoring

                    if running_time > time_limit:
                        err_print(f"The solution exceeded the time limit of {time_limit:.3f}sec; "
                                  f"it didn't finish after {running_time:.3f}sec...")
                        if score > 0: info_print(f"It would have gotten a score of {score} otherwise...")
                        return False, 0.0

                    return correct, score

        correct, score = get_score()
        total += 1
        corrects += correct
        if correct:
            succ_print("File", str(index).rjust(3), 'correct')
        else:
            err_print("File", str(index).rjust(3), 'WRONG' + '!'*11)
        scoresheet.append((index, input_, correct, score))

    decor_print()
    decor_print('.'*42)
    (succ_print if corrects == total else err_print)(str(corrects), end=' ')
    (succ_print if corrects == total else info_print)(f'out of {total} files correct')
    info_print(f'Max running time: {max_time:.2f}sec')
    decor_print('.'*42)
    decor_print()

    # also print subtask grades
    if details.valid_subtasks:
        def get_all_subtasks():
            subtasks = args.subtasks or list(map(str, details.valid_subtasks))
            if os.path.isfile(details.subtasks_files):
                inputs = [input_ for index, input_, *rest in scoresheet]
                subtasks_of, all_subtasks = extract_subtasks(subtasks, details.load_subtasks_files(), inputs=inputs)
            else:
                detector = _get_subtask_detector_from_args(args, purpose='subtask scoring', details=details)
                subtasks_of, all_subtasks = compute_subtasks(subtasks, detector, format=format_)

            # normal grading
            all_subtasks = {sub: {'min_score': 1} for sub in all_subtasks}
            for index, input_, correct, score in scoresheet:
                for sub in subtasks_of[input_]:
                    all_subtasks[sub]['min_score'] = min(all_subtasks[sub]['min_score'], score)

            return all_subtasks

        decor_print()
        decor_print('.'*42)
        beginfo_print('SUBTASK REPORT:')
        for sub, details in natsorted(get_all_subtasks().items()):
            print(info_text("Subtask ="),
                  key_text(str(sub).rjust(4)),
                  info_text(": Score = "),
                  (succ_text if details['min_score'] == 1 else
                   info_text if details['min_score'] > 0 else
                   err_text)(f"{float(details['min_score']):.3f}"),
                  sep='')





##########################################
# just run the solution

run_p = subparsers.add_parser('run',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Run a program against input files (and print to stdout)',
        description=cformat_text(dedent('''\
                Run a program against a set of input files, and print the result to stdout.


                $ [*[kg run -i [input_pattern] -f [solution_program]]*]

                This runs [solution_program] for every file in [input_pattern], and simply forwards its results
                to everything to stdout and stderr.


                For example,

                $ [*[kg run -i "tests/*.in" -f Solution.java]*]

                Quotes are required (at least on Linux), otherwise bash will replace it with the
                actual matched filenames. (not sure about Windows)

                The programming language of the program is inferred from the extension. You can also pass a full
                command using -c, for example,

                $ [*[kg run -i "tests/*.in" -c pypy3 solution.py]*]


                You can also run this for just one file, e.g.,

                $ [*[kg run -i data/sample.in -f solution.cpp]*]

                There can even be multiple "*"s in -i.


                This is useful, for example, if you want to validate a bunch of test files:

                $ [*[kg run -i "tests/*.in" -f Validator.java]*]


                If you wrote your problem using "kg init", then you may omit "-i" and "-f"; they will default to
                the KompGen format ("tests/*.in"), and other details will be parsed from details.json, so
                "[*[kg run]*]" without options would just work. (You can still pass them of course.)


                If your command (-c) requires leading dashes, then the argument parser might interpret them as
                options to "kg run" itself. To work around this, prepend "___" (triple underscore) to each part
                containing a "-". The "___" will be ignored. For example,

                $ [*[kg run -c java ___-Xss128m MyProgram]*]
        ''')))

run_p.add_argument('-F', '--format', '--fmt', help='format of data')
run_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
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

    solution = Program.from_args(args.file, args.command) or details.model_solution
    if not solution: raise CommandError("Missing solution")

    solution.do_compile()
    for input_ in format_.thru_inputs():
        with open(input_) as inp:
            info_print('RUNNING FOR', input_, file=stderr)
            try:
                solution.do_run(stdin=inp, time=True, check=True)
            except CalledProcessError:
                err_print('The program issued a runtime error...', file=stderr)





##########################################
# make everything !!!

make_p = subparsers.add_parser('make',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Create all test data (input+output files) and validate',
        description=cformat_text(dedent('''\
                Create all test data (input+output files), detect subtasks, and perform checks/validations.

                This command is intended for problems created using "kg init". In that case, it will parse the
                relevant information from the details.json file.


                This generates input files from testscript and generator files:

                $ [*[kg make inputs]*]
                $ [*[kg make inputs --validation]*]  # if you want validation


                This generates output files from input files (similar to "kg gen"):

                $ [*[kg make outputs]*]
                $ [*[kg make outputs --checks]*]  # if you want to run the checker


                This detects the subtasks (similar to "kg subtasks") and writes it to the "subtasks_files" file
                in JSON format:

                $ [*[kg make subtasks]*]


                More usage examples:

                $ [*[kg make all]*]  # does all of the above.
                $ [*[kg make inputs outputs --checks]*]  # only inputs and outputs, no validation, with checker.

                Other combinations are also allowed.


                You will probably want to run "kg make all" after finalizing all files---generators, validator,
                checker, etc.---and make sure it finishes without errors. (unless this takes too long...)
        ''')))

make_p.add_argument('makes', nargs='+', help='what to make. (all, inputs, etc.)')
make_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
make_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
make_p.add_argument('-V', '--validation', action='store_true', help="Validate the input files against the validators")
make_p.add_argument('-C', '--checks', action='store_true', help="Check the output file against the checker")

@set_handler(make_p)
def _kg_make(format_, args):
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'make'.")

    details = Details.from_format_loc(format_, args.details, relpath=args.loc)
    kg_make(args.makes, args.loc, format_, details, validation=args.validation, checks=args.checks)

def kg_make(omakes, loc, format_, details, validation=False, checks=False):
    makes = set(omakes)
    valid_makes = {'all', 'inputs', 'outputs', 'subtasks'}
    if not (makes <= valid_makes):
        raise CommandError(f"Unknown make param(s): {ctext(*sorted(makes - valid_makes))}")

    if 'all' in makes:
        makes |= valid_makes
        validation = checks = True

    if 'inputs' in makes:
        decor_print()
        decor_print('~~ '*14)
        beginfo_print('MAKING INPUTS...' + ("WITH VALIDATION..." if validation else 'WITHOUT VALIDATION'))
        if not details.testscript:
            raise CommandError("Missing testscript")

        with open(details.testscript) as scrf:
            script = scrf.read()

        fmt = get_format_from_type(format_, loc, write='i', clear='i')

        if validation:
            validator = details.validator
            validator.do_compile()

        for filename in run_testscript(fmt.thru_expected_inputs(), script, details.generators, relpath=loc):
            if validation:
                info_print('Validating', filename)
                with open(filename) as file:
                    validator.do_run(stdin=file, check=True)

        succ_print('DONE MAKING INPUTS.')

    if 'outputs' in makes:
        decor_print()
        decor_print('~~ '*14)
        beginfo_print('MAKING OUTPUTS...' + ("WITH CHECKS..." if checks else 'WITHOUT CHECKS'))
        fmt = get_format_from_type(format_, loc, read='i', write='o', clear='o')
        generate_outputs(
                fmt, details.judge_data_maker,
                model_solution=details.model_solution,
                judge=details.checker if checks else None,
                interactor=details.interactor)

        succ_print('DONE MAKING OUTPUTS.')

    if 'subtasks' in makes:
        decor_print()
        decor_print('~~ '*14)
        beginfo_print('MAKING SUBTASKS...')
        if not details.valid_subtasks:
            if 'subtasks' in omakes:
                raise CommandError("valid_subtasks list required if you wish to make subtasks")
            else:
                info_print("no valid_subtasks found, so actually, subtasks will not be made. move along.")
        else:
            if not details.subtasks_files:
                raise CommandError(f"A 'subtasks_files' entry in {details.source} is required at this step.")

            detector = details.subtask_detector
            if not detector: raise CommandError("Missing detector/validator")

            # find subtask list
            subtasks = list(map(str, details.valid_subtasks))
            if details.validator and not subtasks: # subtask list required for detectors from validator
                raise CommandError("Missing subtask list")

            # iterate through inputs, run our detector against them
            subtasks_of, all_subtasks = compute_subtasks(
                    subtasks, detector, format=get_format_from_type(format_, loc, read='i'), relpath=loc)

            info_print(f'WRITING TO {details.subtasks_files}')
            details.dump_subtasks_files(construct_subs_files(subtasks_of))

            succ_print('DONE MAKING SUBTASKS.')


def construct_subs_files(subtasks_of):
    prev, lf, rg = None, 0, -1
    for idx, file in enumerate(subtasks_of):
        assert rg == idx - 1
        subs = subtasks_of[file]
        assert subs
        if prev != subs:
            if prev: yield lf, rg, sorted(map(int, prev))
            prev, lf = subs, idx
        rg = idx
    if prev: yield lf, rg, sorted(map(int, prev))





##########################################
q_p = subparsers.add_parser('joke',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Print a non-funny joke',
        description=rand_cformat_text(dedent('''\
                Print a non-funny joke.

                I'm sorry if they're not as funny as your jokes.

                '''))
                + cformat_text('[^[Any]^] [*[help]*] [#[would]#] [.[be].] [%[very]%] [@[much]@] [+[appreciated]+]...'))
qs = [
    '10kg > 1kg > 100g > 10g > log > log log > sqrt log log > 1',
    'Spacewaker',
    # add your jokes here plz
]
@set_handler(q_p)
def kg_q(format_, args):
    import random
    key_print(random.choice(qs))





##########################################
# make a new problem

init_p = subparsers.add_parser('init',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Create a new problem, formatted kg-style',
        description=cformat_text(dedent('''\
                Create a new problem, formatted KompGen-style.

                Use this if you're planning to write everything from scratch (with the help of KompGen).


                $ [*[kg init [problemname]]*]

                This creates a folder [problemname] and prepopulates it with templates. [problemname]
                should only have underscores, dashes, letters, and digits. 

                It also accepts a few options. Examples:


                Basic usage. set up a problem with code "my-problem".
                $ [*[kg init my-problem]*]

                Set the title. Can be changed later (in details.json)
                $ [*[kg init my-problem --title "My Cool Problem"]*]

                "Minimal" setup, i.e., fewer and shorter prepopulated files.
                $ [*[kg init my-problem --minimal]*]
            
                Set up a problem with 5 subtasks.
                $ [*[kg init my-problem --subtasks 5]*]
                
                Include a checker in the prepopulated files.
                $ [*[kg init my-problem --checker]*]

                Set the time limit to 7sec. Can be changed later (in details.json)
                $ [*[kg init my-problem --time-limit 7]*]

                You can also combine options, e.g.,
                $ [*[kg init my-problem --subtasks 5 --minimal --checker -tl 7 -t "My Cool Problem"]*]
        ''')))

init_p.add_argument('problemcode', help='Problem code. Must not contain special characters.')
init_p.add_argument('-l', '--loc', default='.', help='where to make the problem')
init_p.add_argument('-t', '--title', help='Problem title. (Default is generated from problemcode)')
init_p.add_argument('-s', '--subtasks', type=int, default=0, help='Number of subtasks. (0 if binary)')
init_p.add_argument('-m', '--minimal', action='store_true', help="Only put the essentials.")
init_p.add_argument('-c', '--checker', action='store_true', help="Include a checker")
init_p.add_argument('-tl', '--time-limit', type=int, default=2, help='Time limit.')

valid_problemcode = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$')

@set_handler(init_p)
def kg_init(format_, args):
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'init'.")
  
    prob = args.problemcode

    if not valid_problemcode.match(prob):
        raise CommandError("No special characters allowed for the problem code, "
                "and the first and last characters must be a letter or a digit.")

    src = kg_problem_template
    dest = os.path.join(args.loc, prob)

    print(info_text('The destination folder will be'), key_text(dest))
    if os.path.exists(dest):
        raise CommandError("The folder already exists!")

    if args.subtasks < 0:
        raise CommandError("Subtask count must be >= 0")

    touch_dir(dest)

    subtask_list = [OrderedDict(id=index, score=10) for index in range(1, args.subtasks + 1)]
    env = {
        'problem_title': args.title or ' '.join(re.split(r'[-_. ]+', prob)).title().strip(),
        'minimal': args.minimal,
        'checker': args.checker,
        'subtasks': args.subtasks,
        # Jinja's tojson doesn't seem to honor dict order, so let's just use json.dumps
        "subtask_list": [OrderedDict(id=index, score=10) for index in range(1, args.subtasks + 1)],
        'subtask_list_json': json.dumps(subtask_list, indent=4),
        'time_limit': args.time_limit,
        "version": VERSION,
    }

    fmt = Format(os.path.join(src, '*'), os.path.join(dest, '*'), read='i', write='o')
    for inp, outp in fmt.thru_io():
        if not os.path.isfile(inp): continue
        if os.path.splitext(inp)[1] == '.j2':
            res = kg_render_template(inp, **env)
            outp, ext = os.path.splitext(outp)
            assert ext == '.j2'
        else:
            with open(inp) as inpf:
                res = inpf.read()
        touch_container(outp)
        if res.strip('\n'):
            info_print(f'Writing {os.path.basename(outp)}')
            if not res.endswith('\n'): res += '\n'
            with open(outp, 'w') as outpf:
                outpf.write(res)

    succ_print('DONE!')





##########################################
# compile source codes for upload

compile_p = subparsers.add_parser('kompile',
        aliases=['compile'],
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Preprocess python source codes to be ready to upload',
        description=cformat_text(dedent('''\
                Preprocess python source codes to be ready to upload.


                $ [*[kg kompile -f [program_files]]*]


                For example,

                $ [*[kg kompile -f validator.py]*]
                $ [*[kg kompile -f gen_random.py]*]
                $ [*[kg kompile -f checker.py]*]

                Or simultaneously,

                $ [*[kg kompile -f validator.py gen_random.py checker.py]*]


                If you wrote your problem using "kg init", then the usage is very simple:

                $ [*[kg kompile]*]


                It will kompile all relevant files in details.json: model solution, data maker, validator,
                generators, and checker (if they exist).


                Explanation:

                Python files written using KompGen usually imports from other files (and from the "kg" library
                itself), but most contest/judge systems only accept single files. This command "inlines" the
                imports automatically, so that the result is a single file. 

                Any "import star" line ending with the string "### @import" will be replaced inline with the
                code from that file. This works recursively.  

                Only "kg" library commands and files that are explicitly added (in details.json and/or via
                --files/--extra-files) will be inlined. So, if you are importing from a separate file, ensure
                that it is in "other_programs" (or "generators", "model_solution", etc.) or in --extra-files.

                Only Python files will be processed; it is up to you to ensure that the non-python programs you
                write will be compatible with the contest system/judge they are using.

                The generated files will be in "kgkompiled/".  

                Other directives aside from "@import" are available; see the KompGen repo docs for more details.
        ''')))
compile_p.add_argument('formats', nargs='*',
                                help='contest formats to compile to (["hr", "pg", "pc2", "dom", "cms"], default ["pg"])')
compile_p.add_argument('-f', '--files', nargs='*',
                                help='files to compile (only needed if you didn\'t use "kg init")')
compile_p.add_argument('-ef', '--extra-files', nargs='*',
                                help='extra files imported via "@import" (only needed if you didn\'t use "kg init", '
                                'otherwise, please use "other_programs")')
compile_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
compile_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
compile_p.add_argument('-S', '--shift-left', action='store_true',
                                help='compress the program by reducing the indentation size from 4 spaces to 1 tab. '
                                'Use at your own risk. (4 is hardcoded because it is the indentation level of the '
                                '"kg" module.')
compile_p.add_argument('-C', '--compress', action='store_true',
                                help='compress the program by actually compressing it. Use at your own risk.')

@set_handler(compile_p)
def _kg_compile(format_, args):
    if args.main_command == 'compile':
        info_print("You spelled 'kompile' incorrectly. I'll let it slide for now.", file=stderr)

    kg_compile(
        format_,
        Details.from_format_loc(format_, args.details),
        *(args.formats or ['pg']),
        loc=args.loc,
        shift_left=args.shift_left,
        compress=args.compress,
        files=args.files,
        extra_files=args.extra_files,
        )

def kg_compile(format_, details, *target_formats, loc='.', shift_left=False, compress=False, python3='python3',
        dest_loc=None, files=[], extra_files=[]):

    valid_formats = {'hr', 'pg', 'pc2', 'dom', 'cms', 'cms-it'}
    if not set(target_formats) <= valid_formats:
        raise CommandError(f"Invalid formats: {set(target_formats) - valid_formats}")
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'kompile'.")

    # TODO clear kgkompiled first, or at least the target directory

    # convert files to Programs
    files = [Program.from_data(file, relpath=loc) for file in files or []]
    extra_files = [Program.from_data(file, relpath=loc) for file in extra_files or []]

    @memoize
    def get_module(filename):
        if filename and os.path.isfile(filename) and filename.endswith('.py'):
            module, ext = os.path.splitext(os.path.basename(filename))
            assert ext == '.py'
            return module

    @memoize
    @listify
    def load_module(module_id):
        if module_id not in locations:
            raise CommandError(f"Couldn't find module {module_id}! "
                    f"(Add it to {'other_programs' if problem_code else '--extra-files'}?)")
        with open(locations[module_id]) as f:
            for line in f:
                if not line.endswith('\n'):
                    warn_print('Warning:', locations[module_id], "doesn't end with a new line.")
                yield line.rstrip('\n')

    def get_module_id(module, context):
        nmodule = module
        if nmodule.startswith('.'):
            if context['module_id'] in kg_libs:
                nmodule = 'kg' + nmodule

        if nmodule.startswith('.'):
            warn_print(f"Warning: Ignoring relative import for {module}", file=stderr)
            nmodule = nmodule.lstrip('.')

        return nmodule

    # extract problem code
    # not really sure if this is the best way to extract the problem code.
    # also, probably should be put elsewhere...
    if details.relpath:
        problem_code = os.path.basename(os.path.abspath(os.path.join(details.relpath, '.')))
    elif details.source:
        problem_code = os.path.basename(os.path.dirname(os.path.abspath(details.source)))
    elif details.title:
        problem_code = '-'.join(''.join(c if c.isalnum() else ' ' for c in details.title).lower().split())
    else:
        problem_code = None # probably a one-off application

    # locate all necessary files

    # kg libs
    locations = {
        'kg.generators': 'generators.py',
        'kg.validators': 'validators.py',
        'kg.checkers': 'checkers.py',
        'kg.utils': os.path.join('utils', '__init__.py'),
        'kg.utils.hr': os.path.join('utils', 'hr.py'),
        'kg.utils.utils': os.path.join('utils', 'utils.py'),
        'kg.graphs': os.path.join('graphs', '__init__.py'),
        'kg.graphs.utils': os.path.join('graphs', 'utils.py'),
        'kg.graphs.generators': os.path.join('graphs', 'generators.py'),
        'kg.grids': os.path.join('grids', '__init__.py'),
        'kg.grids.utils': os.path.join('grids', 'utils.py'),
        'kg.grids.generators': os.path.join('grids', 'generators.py'),
        'kg.math': os.path.join('math', '__init__.py'),
        'kg.math.geom2d': os.path.join('math', 'geom2d.py'),
        'kg.math.primes': os.path.join('math', 'primes.py'),
    }
    locations = {lib: os.path.join(kg_path, path) for lib, path in locations.items()}
    kg_libs = set(locations)

    checkers = []

    # detect checkers (try to be smart)
    for file in files:
        base, ext = os.path.splitext(os.path.basename(file.rel_filename))
        if 'checker' in base and ext == '.py':
            checkers.append(file)

    if problem_code:
        # current files
        checkers.append(details.checker)

        all_local = [details.validator, details.interactor, details.model_solution] + (
                details.generators + details.other_programs + files + extra_files + checkers)

        # files that start with 'grader.' (for cms mainly)
        graders = [file for file in details.other_programs if os.path.basename(file.filename).startswith('grader.')]

        to_compiles = {
            'pg': [details.validator, details.interactor] + checkers + details.generators,
            'hr': checkers,
            'pc2': [details.validator] + checkers,
            'dom': [details.validator] + checkers,
            'cms': [(checker, "checker") for checker in checkers] + graders,
            'cms-it': [(checker, os.path.join("check", "checker")) for checker in checkers]
                    + [
                        (grader, os.path.join("sol", os.path.basename(grader.rel_filename)))
                        for grader in graders
                    ],
        }
    else:
        all_local = files + extra_files
        to_compiles = {}

    if not problem_code and not files:
        raise CommandError(f"Missing -f/--files. Run 'kg kompile -h' for more details.")

    # keep only python files
    all_local = [p for p in all_local if p and get_module(p.rel_filename)]
    for p in all_local:
        locations[get_module(p.rel_filename)] = p.rel_filename

    # get subtasks files
    subjson = details.subtasks_files
    subtasks_files = []
    if details.valid_subtasks:
        subtasks_files = details.load_subtasks_files()

    def subtask_score(sub):
        if details.valid_subtasks[sub].score is not None:
            return details.valid_subtasks[sub].score
        else:
            default = 10 # hardcoded for now
            warn_print(f'Warning: no score value found for subtask {sub}... using the default {default} points')
            subtask_score.missing = True
            return default
    subtask_score.missing = False

    # convert to various formats
    for fmt, name, copy_files in [
            ('pg', 'Polygon', True),
            ('hr', 'HackerRank', True),
            ('pc2', 'PC2', False),
            ('dom', 'DOMjudge', False),
            ('cms', 'CMS', True),
            ('cms-it', 'CMS Italian', False),
        ]:
        if fmt not in target_formats: continue
        to_compile = files + to_compiles.get(fmt, [])

        problem_template = os.path.join(kg_problem_template, fmt)

        decor_print()
        decor_print('.. '*14)
        beginfo_print(f'Compiling for {fmt} ({name})')
        dest_folder = dest_loc(loc, fmt) if dest_loc else os.path.join(loc, 'kgkompiled', fmt)

        # clear dest_folder (scary...)
        info_print('Clearing folder:', dest_folder, '...')
        if os.path.isdir(dest_folder): rmtree(dest_folder)
        touch_dir(dest_folder)

        to_translate = {}
        to_copy = {}
        for g in to_compile:
            target_name = None
            if isinstance(g, tuple):
                g, target_name = g
            if not g: continue
            if target_name is None:
                target_name = os.path.basename(g.rel_filename)
            if os.path.isfile(g.rel_filename):
                (to_translate if get_module(g.rel_filename) else to_copy)[g.rel_filename] = target_name
            else:
                warn_print(f"Warning: {g.rel_filename} (in details.json) is not a file.", file=stderr)

        targets = {}
        found_targets = {}
        for filename, target_name in to_translate.items():
            module = get_module(filename)
            target = os.path.join(dest_folder, target_name)
            targets[module] = target
            if target in found_targets:
                warn_print(f"Warning: Files have the same destination file ({target}): "
                           f"{found_targets[target]} and {filename}", file=stderr)
            found_targets[target] = filename

        copy_targets = {}
        for filename, target_name in to_copy.items():
            target = os.path.join(dest_folder, target_name)
            copy_targets[filename] = target
            if target in found_targets:
                warn_print(f"Warning: Files have the same destination file ({target}): "
                           f"{found_targets[target]} and {filename}", file=stderr)
            found_targets[target] = filename

        # copying
        for filename in natsorted(to_copy):
            target = copy_targets[filename]
            info_print(f'[... non-python ...] converting {filename} to {target} (kopying only)', file=stderr)
            touch_container(target)
            with open(filename) as srcf, open(target, 'w') as targf:
                targf.write(srcf.read())

        # translating
        for filename in natsorted(to_translate):
            module = get_module(filename)
            info_print(f'[{module}] converting {filename} to {targets[module]} (kompiling)')
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
                        shebang_line = f"#!/usr/bin/env {python3}"
                        info_print(f'adding shebang line {shebang_line!r}')
                        print(shebang_line, file=f)
                    shebanged = True
                    print(line, file=f)
            
            # make it executable
            make_executable(targets[module])


        # TODO for hackerrank, check that the last file for each subtask is unique to that subtask.
        if fmt == 'hr' and details.valid_subtasks:
            try:
                hr_parse_subtasks(details.valid_subtasks, details.load_subtasks_files())
            except HRError:
                err_print("Warning: HackerRank parsing of subtasks failed.")
                raise


        # snippets for hackerrank upload
        if fmt == 'hr':
            for checker in checkers:
                if get_module(checker.rel_filename):
                    # pastable version of grader
                    filename = checker.rel_filename
                    module = get_module(filename)

                    target = os.path.join(dest_folder, 'hr.pastable.version.' + os.path.basename(filename))
                    info_print(f'[{module}] writing snippet version of {filename} to {target}')
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
                        print("# NOTE: THIS SCRIPT IS MEANT TO BE PASTED TO HACKERRANK'S CUSTOM CHECKER, NOT RUN ON ITS OWN.",
                                file=f)
                        for line in lines:
                            assert not line.endswith('\n')
                            print(line, file=f)

                    target = os.path.join(dest_folder, 'hr.subtasks.only.' + os.path.basename(filename))
                    info_print(f'[{module}] writing the subtasks snippet of {filename} to {target}')
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


        # convert testscript
        if fmt == 'pg' and details.testscript:
            filename = details.testscript
            target = os.path.join(dest_folder, os.path.basename(filename))
            info_print(f'[... non-python ...] converting testscript {filename} to {target}', file=stderr)
            touch_container(target)

            with open(details.testscript) as scrf:
                script = scrf.read()

            lines = list(convert_testscript(script, details.generators, relpath=loc))

            with open(target, 'w') as f:
                for line in lines:
                    assert not line.endswith('\n')
                    print(line, file=f)

        # copy over the files
        if copy_files and problem_code:
            info_print('copying test data from', loc, 'to', dest_folder, '...')
            # TODO code this better.
            if fmt == 'cms':
                convert_formats(
                        (format_, loc),
                        (fmt, dest_folder),
                        dest_kwargs=dict(subtasks=subtasks_files)
                    )
            else:
                convert_formats(
                        (format_, loc),
                        (fmt, dest_folder),
                    )


        if fmt == 'dom' and problem_code:
            # statement file
            # just write a dummy file for now, since kompgen doesn't require a pdf file
            # TODO update this when we add 'statement' in details.json
            info_print('creating statement file...')
            source_file = os.path.join(problem_template, 'statement.pdf')
            target_file = os.path.join(dest_folder, 'statement.pdf')
            copy_file(source_file, target_file)

        # do special things for cms
        if fmt == 'cms-it' and problem_code:

            # statement file (required)
            # just write a dummy file for now, since kompgen doesn't require a pdf file
            # TODO update this when we add 'statement' in details.json
            info_print('creating statement file...')
            source_file = os.path.join(problem_template, 'statement.pdf')
            target_file = os.path.join(dest_folder, 'statement', 'statement.pdf')
            copy_file(source_file, target_file)

            # test files
            # need to replicate files that appear in multiple subtasks
            i_os = get_format(argparse.Namespace(format=format_, loc=loc, input=None, output=None), read='io').thru_io()
            if details.valid_subtasks:
                i_o_reps = [i_os[index]
                        for sub in details.valid_subtasks
                        for low, high, subs in subtasks_files
                        if sub in subs
                        for index in range(low, high + 1)]
            else:
                i_o_reps = i_os

            copied = 0
            info_print("Copying now...")
            for (srci, srco), (dsti, dsto) in zip(i_o_reps, CMSItFormat(dest_folder, write='io').thru_expected_io()):
                copy_file(srci, dsti)
                copy_file(srco, dsto)
                copied += 2
            succ_print(f"Copied {copied} files (originally {len(i_os)*2})")

            # task.yaml
            info_print('writing task.yaml')
            if details.valid_subtasks:
                input_count = sum((high - low + 1) * len(subs) for low, high, subs in subtasks_files)
            else:
                input_count = len(CMSItFormat(dest_folder, read='i').inputs)

            kg_render_template_to(
                    os.path.join(problem_template, 'task.yaml.j2'),
                    os.path.join(dest_folder, 'task.yaml'),
                    problem_code=problem_code,
                    details=details,
                    input_count=input_count,
                )

            # gen/GEN
            if details.valid_subtasks:
                info_print('writing gen/GEN (subtasks)')
                gen_file = os.path.join(dest_folder, 'gen', 'GEN')
                touch_container(gen_file)
                with open(gen_file, 'w') as f:
                    total_score = 0
                    index = 0
                    for sub in details.valid_subtasks:
                        score = subtask_score(sub)
                        total_score += score
                        print(f"# ST: {score}", file=f)
                        for low, high, subs in subtasks_files:
                            if sub in subs:
                                for it in range(low, high + 1):
                                    index += 1
                                    print(index, file=f)

                    if index != input_count:
                        raise CommandError("Count mismatch. This shouldn't happen :( Maybe subtasks_files is not up-to-date?")

        if fmt == 'cms' and problem_code:

            # create config file
            config = {
                'name': problem_code,
                'title': details.title,
                'time_limit': details.time_limit,
                'task_type': 'Batch', # only Batch and OutputOnly for now.
                                      # For OutputOnly, just override with cms_options.
                                      # TODO support Communication
                'checker': 'checker',
            }
            if details.valid_subtasks:
                config['score_type'] = 'GroupMin'
                config['score_param'] = [
                    [subtask_score(sub), rf".+_subs.*_{sub}_.*"]
                    for sub in details.valid_subtasks
                ]
                total_score = sum(score for score, *rest in config['score_param'])
            else:
                config['score_type'] = 'Sum'
                config['score_param'] = total_score = 100 # hardcoded for now
            (info_print if total_score == 100 else warn_print)('The total score is', total_score)

            # override options
            config.update(details.cms_options)

            # write config file
            config_file = os.path.join(dest_folder, 'cms_config.json')
            info_print('writing config file...', config_file)
            with open(config_file, 'w') as fl:
                json.dump(config, fl, indent=4)

            tests_folder = os.path.join(dest_folder, 'tests')

            tests_zipname = os.path.join(dest_folder, 'cms_tests.zip')
            info_print('making tests zip for CMS...', tests_zipname)
            def get_arcname(filename):
                assert os.path.samefile(tests_folder, os.path.commonpath([tests_folder, filename]))
                return os.path.relpath(filename, start=tests_folder)
            with zipfile.ZipFile(tests_zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for inp, outp in CMSFormat(dest_folder, read='io').thru_io():
                    for fl in inp, outp:
                        zipf.write(fl, arcname=get_arcname(fl))

            all_zipname = os.path.join(dest_folder, 'cms_all.zip')
            info_print('making whole zip for CMS...', all_zipname)
            with zipfile.ZipFile(all_zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fl in ([tests_zipname, config_file] + [
                            os.path.join(dest_folder, filename)
                            for filename in ['checker'] + [os.path.basename(grader.filename) for grader in graders]
                        ]):
                    zipf.write(fl, arcname=os.path.basename(fl))

        if fmt == 'pg' and problem_code:
            zipname = os.path.join(dest_folder, 'upload_this_to_polygon_but_rarely.zip')
            info_print('making zip for Polygon...', zipname)
            tests_folder = os.path.join(dest_folder, 'tests')
            def get_arcname(filename):
                assert os.path.samefile(tests_folder, os.path.commonpath([tests_folder, filename]))
                return os.path.relpath(filename, start=tests_folder)
            with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for inp in PGFormat(dest_folder, read='i').thru_inputs():
                    zipf.write(inp, arcname=get_arcname(inp))

        if fmt == 'hr' and problem_code:
            zipname = os.path.join(dest_folder, 'upload_this_to_hackerrank.zip')
            info_print('making zip for HackerRank...', zipname)
            def get_arcname(filename):
                assert os.path.samefile(dest_folder, os.path.commonpath([dest_folder, filename]))
                return os.path.relpath(filename, start=dest_folder)
            with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for inp, outp in HRFormat(dest_folder, read='io').thru_io():
                    for fl in inp, outp:
                        zipf.write(fl, arcname=get_arcname(fl))

        succ_print(f'Done compiling problem "{problem_code}"" for {fmt} ({name})')

    decor_print('.. '*14)

    if subtask_score.missing:
        warn_print('Warning: some subtask scores missing. You may want to turn "valid_subtasks" into a list that '
                'looks like [{"id": 1, "score": 20}, {"id": 2, "score": 30}] ...')

    if 'cms-it' in target_formats and details.valid_subtasks and total_score != 100:
        err_print(f'ERROR: The total score is {total_score} but the Italian format requires a total score of 100.')
        raise CommandError(f'The total score is {total_score} but the Italian format requires a total score of 100.')






##########################################
# compile a contest from a configuration file

contest_p = subparsers.add_parser('kontest',
            aliases=['contest'],
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Compile a contest from a description JSON file',
        description=cformat_text(dedent('''\
                Compile a contest from a description JSON file.

                This command is intended for contests whose problems are created using "kg init". In that case,
                it will parse the relevant information from the corresponding details.json files.


                $ [*[kg contest [format] [config_file]]*]

                Here, [format] is the contest format, and [config_file] is a path to a json file containing the
                contest metadata. 

                An example [config_file] can be seen in examples/contest.json.


                In the case of pc2, this generates a folder in "kgkompiled/" containing the files relevant for the
                contest (including seating arrangements [optional] and passwords) and which can be read by the PC^2
                system. Loading it via PC^2 will automatically set up the whole contest. (Painless!)


                This assumes that "kg make all" has been run for every problem. If you wish to run those
                automatically as well, use

                $ [*[kg contest [format] [config_file] --make-all]*]


                Important note about the "--target-loc [target_loc]" option: The [target_loc] must be an absolute
                path pointing to a folder and denotes the location where the contest folder going to be in the
                contest system. The output of "kg contest" will still be generated in "kgkompiled/", but the output
                itself will be configured as if it will be placed in [target_loc] when it is used. This is useful
                since PC^2 requires absolute paths in its configuration.


                See the KompGen repo docs for more details.
        ''')))
contest_p.add_argument('format', help='Contest format to compile to ("pc2", "dom", etc.)')
contest_p.add_argument('config', help='JSON file containing the contest configuration')
contest_p.add_argument('-m', '--make-all', action='store_true', help='Run "kg make all" in all problems')
contest_p.add_argument('-ns', '--no-seating', action='store_true', help='Skip the creation of the seating arrangement')
contest_p.add_argument('-t', '--target-loc', help='Specify the final location of the contest folder in the contest system')
contest_p.add_argument('-s', '--seed', type=int, help='Initial seed to use')

def problem_letters():
    for l in count(1):
        for c in ascii_uppercase:
            yield l * c

@set_handler(contest_p)
def kg_contest(format_, args):
    if args.main_command == 'contest':
        info_print("You spelled 'kontest' incorrectly. I'll let it slide for now.", file=stderr)

    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'kontest'.")

    valid_formats = {'pc2', 'cms', 'cms-it', 'dom'}
    if args.format not in valid_formats:
        raise CommandError(f"Unsupported contest format: {args.format}")

    contest = ContestDetails.from_loc(args.config)

    target_loc = args.target_loc or contest.target_loc or os.path.abspath('kgkompiled')
    if not os.path.isabs(target_loc):
        raise CommandError(f"--target-loc must be an absolute path: got {target_loc!r}")
    info_print(f"Using target_loc = {target_loc!r}", file=stderr)

    seedval = args.seed
    if seedval is None: seedval = contest.seed
    if seedval is None: seedval = randrange(10**18)
    info_print(f"Using seedval = {seedval!r}", file=stderr)
    rand = Random(seedval)

    contest_folder = os.path.join('kgkompiled', contest.code)

    # clear contest_folder (scary...)
    info_print('Clearing folder:', contest_folder, '...')
    if os.path.isdir(contest_folder): rmtree(contest_folder)
    touch_dir(contest_folder)


    decor_print()
    decor_print('-'*42)
    beginfo_print('Making passwords')
    passwords = write_passwords_format(contest, args.format, seedval=seedval, dest=contest_folder)
    succ_print('Done passwords')

    contest_template = os.path.join(kg_contest_template, args.format)

    if args.format == 'cms-it':

        # identify key folders
        contest_data_folder = os.path.join(contest_folder, 'contest')

        # construct template environment
        # TODO pass 'contest' instead of all these
        env = {
            "datetime_created": datetime.now(),
            "contest": contest,
            "passwords": passwords,
        }

        # problem envs
        found_codes = {}
        for letter, problem_loc in zip(problem_letters(), contest.rel_problems):
            details = Details.from_format_loc(format_, os.path.join(problem_loc, 'details.json'), relpath=problem_loc)

            code_raw = os.path.basename(problem_loc)
            code = ''.join(code_raw.split('._-')) # TODO check if this is necessary.
            if code in found_codes:
                found_codes[code] += 1
                code += str(found_codes[code])
            else:
                found_codes[code] = 1
            decor_print()
            decor_print('-'*42)
            print(beginfo_text("Getting problem"), key_text(repr(code)), beginfo_text(f"(from {problem_loc})"))

            if args.make_all:
                info_print('Running "kg make all"...')
                kg_make(['all'], problem_loc, format_, details)

            info_print('Running "kg kompile"...')
            def dest_loc(loc, fmt):
                return os.path.join(contest_data_folder, code)
            kg_compile(format_, details, 'cms-it', loc=problem_loc, dest_loc=dest_loc)

        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing contest config file')
        info_print('Writing contest.yaml')
        source = os.path.join(contest_template, 'contest.yaml.j2')
        target = os.path.join(contest_data_folder, 'contest.yaml')
        kg_render_template_to(source, target, **env)



    if args.format == 'pc2' or args.format == 'dom':

        # identify key folders
        # folder in the judge computers where the files will eventually go in (needed for PC2)
        target_folder = os.path.join(target_loc, contest.code)

        if args.format == 'pc2':
            problems_folder = os.path.join(contest_folder, 'CDP', 'config')
            ext_data = os.path.join(contest_folder, 'ALLDATA')
            target_problems_folder = os.path.join(target_folder, 'CDP', 'config')
            target_ext_data = os.path.join(target_folder, 'ALLDATA')
        else:
            problems_folder = os.path.join(contest_folder, 'PROBLEMS')
            target_problems_folder = os.path.join(target_folder, 'PROBLEMS')
            target_ext_data = None

        # construct template environment
        if not contest.site_password: raise CommandError(f"site_password required for {args.format}")
        # TODO pass 'contest' instead of all these
        env = {
            "datetime_created": datetime.now(),
            "contest": contest,
            "filename": "{:mainfile}",
            "filename_base": "{:basename}",
            "alldata": target_ext_data,
            "problems": [],
        }

        # load colors
        def css_colors():
            with open(os.path.join(kg_data_path, 'css_colors.txt')) as file:
                css_colors = [line.strip() for line in file]
            rand.shuffle(css_colors)
            while True: yield from css_colors
        css_colors = css_colors()

        # problem envs
        found_codes = {}
        letters = []
        for letter, problem_loc in zip(problem_letters(), contest.rel_problems):
            details = Details.from_format_loc(format_, os.path.join(problem_loc, 'details.json'), relpath=problem_loc)

            problem_code_raw = os.path.basename(problem_loc)
            problem_code = ''.join(problem_code_raw.split('._-')) # TODO check if this is necessary.
            if problem_code in found_codes:
                found_codes[problem_code] += 1
                problem_code += str(found_codes[problem_code])
            else:
                found_codes[problem_code] = 1
            decor_print()
            decor_print('-'*42)
            print(beginfo_text("Getting problem"), key_text(repr(problem_code)), beginfo_text(f"(from {problem_loc})"))

            if details.valid_subtasks:
                warn_print(f"Warning: The problem has subtasks, but '{args.format}' contests only support binary tasks. "
                        "Ignoring subtasks.")

            if args.make_all:
                info_print('Running "kg make all"...')
                kg_make(['all'], problem_loc, format_, details)

            time_limit = int(round(details.time_limit))
            if time_limit != details.time_limit:
                raise TypeError(f"The time limit must be an integer for {args.format}: {problem_loc} {time_limit}")

            letters.append(letter)
            problem = {
                'problem_loc': problem_loc,
                'details': details,
                'letter': letter,
                'problem_code_raw': problem_code_raw,
                'problem_code': problem_code,
                'time_limit': time_limit,
                'color': next(css_colors),
            }

            # put validator in input_validators/, and checker to output_validators/
            for name, targ in [
                    ('validator', 'input_validators'),
                    ('checker', 'output_validators'),
                ]:
                src = getattr(details, name)
                # TODO handle the case where src is not Python.
                # We need to compile it and "pass the compiled file" somehow.
                srcf = os.path.join(problem_loc, 'kgkompiled', args.format, os.path.basename(src.filename)) 
                rel_targf = os.path.join(problem_code, targ, os.path.basename(src.filename))
                targf = os.path.join(problems_folder, rel_targf)
                info_print('Copying', srcf, 'to', targf)
                copy_file(srcf, targf)
                make_executable(targf)
                problem[name] = os.path.join(target_problems_folder, rel_targf)

            env['problems'].append(problem)

            # TODO actually organize the code better so we don't have lots of variables in the same scope...
            del letter, details, problem_loc, problem, time_limit, problem_code_raw, problem_code

        def yaml_lang(lang):
            # TODO fix this?
            lenv = {key: (
                value.format(**env) if isinstance(value, str) else
                str(value).lower() if isinstance(value, bool) else value) for key, value in lang.items()}
            run = lenv['run'] + ' '
            spacei = run.index(' ')
            lenv.update({
                    "run_first": run[:spacei],
                    "run_rest": run[spacei+1:-1]
                })
            return lenv

        env['langs'] = [yaml_lang(lang) for lang in contest.langs]

        if args.format == 'pc2':
            decor_print()
            decor_print('-'*42)
            beginfo_print('Writing contest config files')
            for file in ['contest.yaml', 'problemset.yaml']:
                info_print('Writing', file)
                source = os.path.join(contest_template, file + '.j2')
                target = os.path.join(problems_folder, file)
                kg_render_template_to(source, target, **env)

        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing problem files')
        for problem in env['problems']:
            letter = problem['letter']
            problem_code = problem['problem_code']
            details = problem['details']
            problem_loc = problem['problem_loc']

            # write config files
            problem_files = ['problem.yaml']
            if args.format == 'dom':
                problem_files.append('domjudge-problem.ini')
            else:
                problem_files.append(os.path.join('problem_statement', 'problem.tex'))
            for file in problem_files:
                info_print('Writing', file, 'for', problem_code)
                source = os.path.join(contest_template, os.path.basename(file) + '.j2')
                target = os.path.join(problems_folder, problem_code, file)
                kg_render_template_to(source, target, **{**env, **problem})

            kg_compile(format_, details, args.format, loc=problem_loc, python3=contest.python3_command)


            # copy statement. for now, dummy, but in the future, include cms.
            # we will also have global_statements
            if args.format == 'dom':
                source = os.path.join(problem_loc, 'kgkompiled', args.format, 'statement.pdf')
                target = os.path.join(problems_folder, problem_code, 'problem_statement', 'statement.pdf')
                copy_file(source, target)
                target = os.path.join(problems_folder, problem_code, 'problem.pdf')
                copy_file(source, target)


            if args.format == 'dom':
                for name, targ in [
                        ('validator', 'input_validators'),
                        ('checker', 'output_validators'),
                    ]:
                    # TODO assumes python. careful: abs path issues
                    # TODO make this better
                    # I think this part is easier to adjust to handle non-python code
                    # needs to use src.compile and src.run and should use a 'build' file instead of just 'run'
                    # (but again be careful of abs path issues)

                    info_print('Creating run file for', name)
                    source_f = os.path.join(contest_template, 'run.j2')
                    target_f = os.path.join(problems_folder, problem_code, targ, 'run')
                    kg_render_template_to(source_f, target_f, **{**env, **problem})

                    make_executable(target_f)

                    dest = os.path.join(contest_folder, 'UPLOADS', 'UPLOAD_1ST_executables', f'{name}_{problem_code}')
                    info_print('Zipping', name, 'to', f'{dest}.zip')
                    make_archive(dest, 'zip', os.path.join(problems_folder, problem_code, targ))

            # copy model solution
            info_print("Copying model solution")
            source = problem['details'].model_solution.rel_filename
            target = os.path.join(problems_folder, problem_code, 'submissions', 'accepted', os.path.basename(source))
            copy_file(source, target)

            # copy test data
            info_print(f"Copying data for {problem_code}...")
            try:
                src_format = KGFormat(problem['problem_loc'], read='io')
            except FormatError as exc:
                raise CommandError(f"No tests found for '{problem['problem_loc']}'. Please run 'kg make all' "
                        "to generate the files, or call 'kg kontest' with the '-m' option.") from exc
            data_locs = [
                os.path.join(problems_folder, problem_code, 'data', 'secret'),
            ]
            if args.format == 'pc2':
                data_locs.append(os.path.join(ext_data, problem_code))
            for data_loc in data_locs:
                info_print("Copying to", data_loc)
                dest_format = KGFormat(write='io', tests_folder=data_loc)
                copied = 0
                for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
                    copy_file(srci, dsti)
                    copy_file(srco, dsto)
                    copied += 2
                succ_print("Copied", copied, "files")

            if args.format == 'dom':
                # zip the whole problem folder (for upload)
                dest = os.path.join(contest_folder, 'UPLOADS', 'UPLOAD_2ND_problems', problem_code)
                
                info_print('Zipping the whole thing...')
                print(info_text('target is'), key_text(dest + '.zip'))
                make_archive(dest, 'zip', os.path.join(problems_folder, problem_code))
                info_print('Done.')


    if not args.no_seating and contest.seating:
        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing seating arrangement')
        write_seating(contest, seedval=seedval, dest=contest_folder)

    if args.format == 'dom':
        warn_print("Note: There seems to be no way to import contest configuration to DOMjudge")
        warn_print("so you'll have to do that manually.")

    decor_print()
    decor_print('-'*42)
    succ_print('See docs/CONTEST.md for the next steps to finish preparing the contest.')





##########################################
# manage seating arrangements

seating_args(subparsers)





##########################################
# Generate passwords

passwords_p = subparsers.add_parser('passwords',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Assign passwords to a list of teams',
        description=cformat_text(dedent('''\
                Assign passwords to a list of teams.


                $ [*[kg contest [teams_file]]*]

                Here, [teams_file] is a path to a json file containing the team information. Outputs the contest
                data in kgkompiled/.

                It can simply contain a JSON list of strings denoting team names, like:

                [*[[
                    "Quiwarriors 1",
                    "Quiwarriors 2",
                    "Fuchsia Moth",
                    "Re:Programmers"
                ]]*]

                They can also be grouped by school; see examples/teams.json for an example. The printable html
                files generated in kgkompiled/ will include the school name in the output.
        ''')))
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

    beginfo_print(f'Writing passwords for {len(team_names)} teams')
    write_passwords(list(get_accounts()), dest='kgkompiled',
            seedval=' or '.join({str(x) for x in [args.seed, seed] if x is not None}),
            code=args.code, title=args.title)
    succ_print(f'Passwords done')





def set_default_subparser(self, name, args=None, positional_args=0):
    """default subparser selection. Call after setup, just before parse_args()
    name: is the name of the subparser to call by default
    args: if set is the argument list handed to parse_args()

    , tested with 2.7, 3.2, 3.3, 3.4
    it works with 2.6 assuming argparse is installed
    """
    subparser_found = False
    existing_default = False # check if default parser previously defined
    for arg in sys.argv[1:]:
        if arg in ['-h', '--help']:  # global help if no subparser
            break
    else:
        for x in self._subparsers._actions:
            if not isinstance(x, argparse._SubParsersAction):
                continue
            for sp_name in x._name_parser_map.keys():
                if sp_name in sys.argv[1:]:
                    subparser_found = True
                if sp_name == name: # check existance of default parser
                    existing_default = True
        if not subparser_found:
            # If the default subparser is not among the existing ones,
            # create a new parser.
            # As this is called just before 'parse_args', the default
            # parser created here will not pollute the help output.

            if not existing_default:
                for x in self._subparsers._actions:
                    if not isinstance(x, argparse._SubParsersAction):
                        continue
                    x.add_parser(name)
                    break # this works OK, but should I check further?

            # insert default in last position before global positional
            # arguments, this implies no global options are specified after
            # first positional argument
            if args is None:
                sys.argv.insert(len(sys.argv) - positional_args, name)
            else:
                args.insert(len(args) - positional_args, name)

argparse.ArgumentParser.set_default_subparser = set_default_subparser







##########################################
autocomplete(parser)
def main(format='kg'):
    args = parser.parse_args()
    if args.krazy: set_krazy(True)
    logf = stderr
    try:
        logf = args.default_file
        decor_print('\n' + '='*42 + '\n', file=logf)
        args.handler(format, args)
        decor_print('\n' + '='*42 + '\n', file=logf)
        succ_print('THE COMMAND FINISHED SUCCESSFULLY.', file=logf)
    except Exception:
        err_print('THE COMMAND FAILED.', file=logf)
        raise
