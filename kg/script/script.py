from collections import defaultdict
from datetime import datetime
from functools import wraps
from html.parser import HTMLParser
from operator import attrgetter
from random import randrange
from shutil import copyfile
from string import ascii_letters, ascii_uppercase, digits
from subprocess import PIPE, CalledProcessError, SubprocessError, TimeoutExpired
from sys import stdin, stdout, stderr
from textwrap import dedent
import argparse
import contextlib
import os.path
import re
import tempfile
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

                    - (for problems) [*[kg gen]*], [*[kg test]*], [*[kg run]*], [*[kg subtasks]*]
                    - (for contests) [*[kg seating]*], [*[kg passwords]*]
                    - (others) [*[kg convert]*], [*[kg convert-sequence]*]

                - For developing problems/contests from scratch (writing generators, validators, checkers, etc.)

                    - (for problems) [*[kg init]*], [*[kg make]*], [*[kg gen]*]/[*[test]*]/[*[run]*], [*[kg compile]*]
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

def convert_formats(src, dest):
    sformat, sloc = src
    dformat, dloc = dest
    src_format = get_format(argparse.Namespace(format=sformat, loc=sloc, input=None, output=None), read='io')
    dest_format = get_format(argparse.Namespace(format=dformat, loc=dloc, input=None, output=None), write='io')

    copied = 0
    info_print("Copying now...")
    for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
        touch_container(dsti)
        touch_container(dsto)
        copyfile(srci, dsti)
        copyfile(srco, dsto)
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
        touch_container(destf)
        copyfile(srcf, destf)
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
    if not detector: raise CommandError("Missing detector/validator")
    # find subtask list
    subtasks = args.subtasks or list(map(str, details.valid_subtasks))

    if validator and not subtasks: # subtask list required for detectors from validator
        raise CommandError("Missing subtask list")

    get_subtasks(subtasks, detector, format_)

def get_subtasks(subtasks, detector, format_, relpath=None):
    subtset = set(subtasks)

    # iterate through inputs, run our detector against them
    subtasks_of = {}
    all_subtasks = set()
    files_of_subtask = {sub: set() for sub in subtset}
    detector.do_compile()
    inputs = []
    for input_ in format_.thru_inputs():
        inputs.append(input_)
        with open(input_) as f:
            try:
                result = detector.do_run(*subtasks, stdin=f, stdout=PIPE, check=True)
            except CalledProcessError as cpe:
                err_print(f"The detector raised an error for {input_}", file=stderr)
                raise CommandError(f"The detector raised an error for {input_}") from cpe
        subtasks_of[input_] = set(result.stdout.decode('utf-8').split())
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

    return subtasks_of, all_subtasks, inputs





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

    solution.do_compile()
    judge.do_compile()
    if interactor: interactor.do_compile()
    total = corrects = 0
    scoresheet = []
    max_time = 0
    for index, (input_, output_) in enumerate(format_.thru_io()):
        def get_score():
            nonlocal max_time
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
                        max_time = max(max_time, solution.last_running_time)

                    # Check if the interactor issues WA by itself. Don't invoke the judge
                    if getattr(interactor_res, 'returncode', 0):
                        err_print('The interactor did not accept the interaction...')
                        return False, 0.0

                    jargs = list(map(os.path.abspath, (input_, tmp.name, output_)))
                    if not args.judge_strict_args:
                        jargs += [result_tmp.name, '-c', solution.filename, '-t', str(index), '-v']

                    correct = judge.do_run(*jargs, check=False).returncode == 0
                    try:
                        with open(result_tmp.name) as result_tmp_file:
                            score = json.load(result_tmp_file)['score']
                    except Exception as exc:
                        score = 1.0 if correct else 0.0 # can't read score. use binary scoring

                    if solution.last_running_time > time_limit:
                        err_print(f"The solution exceeded the time limit of {time_limit:.3f}sec; "
                                  f"it didn't finish after {solution.last_running_time:.3f}sec...")
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
    info_print(f'Max running time (from time.time()): {max_time:.2f}sec')
    decor_print('.'*42)
    decor_print()

    # also print subtask grades
    if details.valid_subtasks:
        validator = Program.from_args(args.validator_file, args.validator_command)
        detector = None
        if validator:
            detector = detector_from_validator(validator)
            assert detector
            info_print("Found a validator.", end=' ')
        elif details.subtask_detector:
            detector = details.subtask_detector
            info_print(f"Found a detector in {details.source}.", end=' ')
        if detector:
            info_print('Proceeding with subtask grading...')
            # find subtask list
            subtasks = args.subtasks or list(map(str, details.valid_subtasks))
            if validator and not subtasks: # subtask list required for detectors from validator
                raise CommandError("Missing subtask list (for subtask grading)")
            subtasks_of, all_subtasks, inputs = get_subtasks(subtasks, detector, format_)
            # normal grading
            min_score = {sub: 1 for sub in all_subtasks}
            for index, input_, correct, score in scoresheet:
                for sub in subtasks_of[input_]:
                    min_score[sub] = min(min_score[sub], score)

            decor_print()
            decor_print('.'*42)
            beginfo_print('SUBTASK REPORT:')
            for sub in natsorted(all_subtasks):
                print(info_text("Subtask ="),
                      key_text(str(sub).rjust(4)),
                      info_text(": Score = "),
                      (succ_text if min_score[sub] == 1 else
                       info_text if min_score[sub] > 0 else
                       err_text)(f"{float(min_score[sub]):.3f}"),
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
            subtasks_of, all_subtasks, inputs = get_subtasks(
                    subtasks, detector, get_format_from_type(format_, loc, read='i'), relpath=loc)

            info_print(f'WRITING TO {details.subtasks_files}')
            details.dump_subtasks_files(construct_subs_files(subtasks_of, inputs))

            succ_print('DONE MAKING SUBTASKS.')


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

    src = os.path.join(kg_data_path, 'template')
    dest = os.path.join(args.loc, prob)

    print(info_text('The destination folder will be'), key_text(dest))
    if os.path.exists(dest):
        raise CommandError("The folder already exists!")

    if args.subtasks < 0:
        raise CommandError("Subtask count must be >= 0")

    touch_dir(dest)

    env = {
        'problem_title': args.title or ' '.join(re.split(r'[-_. ]+', prob)).title().strip(),
        'minimal': args.minimal,
        'checker': args.checker,
        'subtasks': args.subtasks,
        'subtask_list': list(range(1, args.subtasks + 1)),
        'time_limit': args.time_limit,
        "version": VERSION,
    }

    fmt = Format(os.path.join(src, '*'), os.path.join(dest, '*'), read='i', write='o')
    for inp, outp in fmt.thru_io():
        if not os.path.isfile(inp): continue
        with open(inp) as inpf:
            res = inpf.read()
        if os.path.splitext(inp)[1] == '.j2':
            res = Template(res).render(**env)
            outp, ext = os.path.splitext(outp)
            assert ext == '.j2'
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

                This command is intended for problems created using "kg init". In that case, it will parse the
                relevant information from the details.json file.


                The usage is very simple:

                $ [*[kg kompile]*]


                Explanation:

                Python files written using KompGen usually imports from other files (and from the "kg" library
                itself), but most contest/judge systems only accept single files. This command "inlines" the
                imports automatically, so that the result is a single file. 

                Any "import star" line ending with the string "### @import" will be replaced inline with the
                code from that file. This works recursively.  

                Only "kg" library commnds and files explicitly added in details.json will be inlined. So if you
                are importing from a separate file, ensure that it is in "other_programs" (or "generators",
                "model_solution", etc.)

                Only Python files will be processed; it is up to you to ensure that the non-python programs you
                write will be compatible with the contest system/judge they are using.

                The generated files will be in "kgkompiled/".  

                Other directives aside from "@import" are available; see the KompGen repo docs for more details.
        ''')))
compile_p.add_argument('formats', nargs='*', help='contest formats to compile to (default ["hr", "pg", "pc2"])')
compile_p.add_argument('-l', '--loc', default='.', help='location to run commands on')
compile_p.add_argument('-d', '--details', help=argparse.SUPPRESS)
compile_p.add_argument('-S', '--shift-left', action='store_true',
                                help='compress the program by reducing the indentation size from 4 spaces to 1 tab. '
                                'Use at your own risk. (4 is hardcoded because it is the indentation level of the '
                                '"kg" module.')
compile_p.add_argument('-C', '--compress', action='store_true',
                                help='compress the program by actually compressing it. Use at your own risk.')
# TODO add option for format to "compile" to. No need for now since there are only a few,
#      but later on this will eat up a lot of memory otherwise.

@set_handler(compile_p)
def _kg_compile(format_, args):
    if args.main_command == 'compile':
        info_print("You spelled 'kompile' incorrectly. I'll let it slide for now.", file=stderr)

    kg_compile(
        format_,
        Details.from_format_loc(format_, args.details),
        *(args.formats or ['hr', 'pg', 'pc2']),
        loc=args.loc,
        shift_left=args.shift_left,
        compress=args.compress,
        )

def kg_compile(format_, details, *target_formats, loc='.', shift_left=False, compress=False, python3='python3'):
    valid_formats = {'hr', 'pg', 'pc2'}
    if not set(target_formats) <= valid_formats:
        raise CommandError(f"Invalid formats: {set(target_formats) - valid_formats}")
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'kompile'.")

    # TODO clear kgkompiled first, or at least the target directory

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
        'kg.math.primes': os.path.join('math', 'primes.py'),
    }
    locations = {lib: os.path.join(kg_path, path) for lib, path in locations.items()}
    kg_libs = set(locations)

    # current files
    all_local = [details.validator, details.checker, details.interactor, details.model_solution] + (
            details.generators + details.other_programs)

    @memoize
    def get_module(filename):
        if filename and os.path.isfile(filename) and filename.endswith('.py'):
            module, ext = os.path.splitext(os.path.basename(filename))
            assert ext == '.py'
            return module

    # keep only python files
    all_local = [p for p in all_local if p and get_module(p.rel_filename)]
    for p in all_local:
        locations[get_module(p.rel_filename)] = p.rel_filename

    @memoize
    @listify
    def load_module(module_id):
        if module_id not in locations:
            raise CommandError(f"Couldn't find module {module_id}! (Add it to other_programs?)")
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

    # get subtasks files
    subjson = details.subtasks_files
    subtasks_files = []
    if details.valid_subtasks:
        subtasks_files = details.load_subtasks_files()

    # convert to various formats
    for fmt, name, copy_files, to_compile in [
            ('pg', 'Polygon', True, [details.validator, details.interactor, details.checker] + details.generators),
            ('hr', 'HackerRank', True, [details.checker]),
            ('pc2', 'PC2', False, [details.validator, details.checker]),
        ]:
        if fmt not in target_formats: continue

        decor_print()
        decor_print('.. '*14)
        beginfo_print(f'Compiling for {fmt} ({name})')
        dest_folder = os.path.join(loc, 'kgkompiled', fmt)
        to_translate = set()
        to_copy = set()
        for g in to_compile:
            if not g: continue
            if os.path.isfile(g.rel_filename):
                (to_translate if get_module(g.rel_filename) else to_copy).add(g.rel_filename)
            else:
                warn_print(f"Warning: {g.rel_filename} (in details.json) is not a file.", file=stderr)

        targets = {}
        found_targets = {}
        for filename in to_translate:
            module = get_module(filename)
            target = os.path.join(dest_folder, os.path.basename(filename))
            targets[module] = target
            if target in found_targets:
                warn_print(f"Warning: Files have the same destination file ({target}): "
                           f"{found_targets[targets]} and {filename}", file=stderr)
            found_targets[target] = filename

        copy_targets = {}
        for filename in to_copy:
            target = os.path.join(dest_folder, os.path.basename(filename))
            copy_targets[filename] = target
            if target in found_targets:
                warn_print(f"Warning: Files have the same destination file ({target}): "
                           f"{found_targets[targets]} and {filename}", file=stderr)
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

        # TODO for hackerrank, check that the last file for each subtask is unique to that subtask.
        if fmt == 'hr' and details.valid_subtasks:
            try:
                hr_parse_subtasks(details.valid_subtasks, details.load_subtasks_files())
            except HRError:
                err_print("Warning: HackerRank parsing of subtasks failed.")
                raise



        if fmt == 'hr' and details.checker and get_module(details.checker.rel_filename): # snippets for hackerrank upload.
            # pastable version of grader
            filename = details.checker.rel_filename
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
        if copy_files:
            info_print('copying test data from', loc, 'to', dest_folder, '...')
            convert_formats(
                    (format_, loc),
                    (fmt, dest_folder),
                )

        if fmt == 'pg':
            zipname = os.path.join(dest_folder, 'upload_this_to_polygon.zip')
            info_print('making zip for Polygon...', zipname)
            tests_folder = os.path.join(dest_folder, 'tests')
            def get_arcname(filename):
                assert os.path.samefile(tests_folder, os.path.commonpath([tests_folder, filename]))
                return os.path.relpath(filename, start=tests_folder)
            with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for inp in PGFormat(dest_folder, read='i').thru_inputs():
                    zipf.write(inp, arcname=get_arcname(inp))

        if fmt == 'hr':
            zipname = os.path.join(dest_folder, 'upload_this_to_hackerrank.zip')
            info_print('making zip for HackerRank...', zipname)
            def get_arcname(filename):
                assert os.path.samefile(dest_folder, os.path.commonpath([dest_folder, filename]))
                return os.path.relpath(filename, start=dest_folder)
            with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for inp, outp in HRFormat(dest_folder, read='io').thru_io():
                    for fl in inp, outp:
                        zipf.write(fl, arcname=get_arcname(fl))

        succ_print(f'Done for {fmt} ({name})')

    decor_print('.. '*14)





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

                Here, [format] is the contest format (currently, only "pc2" is supported), and [config_file] is a
                path to a json file containing the contest metadata. 

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
contest_p.add_argument('format', help='Contest format to compile to')
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

    if args.format != 'pc2':
        raise CommandError(f"Unsupported contest format: {args.format}")

    # TODO possibly use a yaml library here, but for now this will do.
    contest = ContestDetails.from_loc(args.config)

    target_loc = args.target_loc or contest.target_loc or os.path.abspath('kgkompiled')
    if not os.path.isabs(target_loc):
        raise CommandError(f"--target-loc must be an absolute path: got {target_loc!r}")
    info_print(f"Using target_loc = {target_loc!r}", file=stderr)

    seedval = args.seed
    if seedval is None: seedval = contest.seed
    if seedval is None: seedval = randrange(10**18)
    info_print(f"Using seedval = {seedval!r}", file=stderr)

    if args.format == 'pc2':

        # identify key folders
        contest_folder = os.path.join('kgkompiled', contest.code)
        cdp_config = os.path.join(contest_folder, 'CDP', 'config')
        ext_data = os.path.join(contest_folder, 'ALLDATA')
        contest_template = os.path.join(kg_data_path, 'contest_template', 'pc2')

        target_folder = os.path.join(target_loc, contest.code)
        target_cdp_config = os.path.join(target_folder, 'CDP', 'config')
        target_ext_data = os.path.join(target_folder, 'ALLDATA')

        # construct template environment
        if not contest.site_password: raise CommandError("site_password required for PC2")
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
            "alldata": target_ext_data,
        }

        # problem envs
        found_codes = {}
        problem_env = {}
        letters = []
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

            if details.valid_subtasks:
                warn_print("Warning: The problem has subtasks, but 'pc2' contests only support binary tasks. "
                        "Ignoring subtasks.")

            if args.make_all:
                info_print('Running "kg make all"...')
                kg_make(['all'], problem_loc, format_, details)

            time_limit = int(round(details.time_limit))
            if time_limit != details.time_limit:
                raise TypeError(f"The time limit must be an integer for PC2: {problem_loc} {time_limit}")

            letters.append(letter)
            problem_env[letter] = {
                'problem_loc': problem_loc,
                'details': details,
                'letter': letter,
                'problem_code_raw': code_raw,
                'problem_code': code,
                'title': details.title,
                'letter_title': f'{letter}: {details.title}',
                'time_limit': time_limit,
            }

            # put validator in input_validators/, and checker to output_validators/
            kg_compile(format_, details, 'pc2', loc=problem_loc, python3=contest.python3_command)
            for name, targ in [
                    ('validator', 'input_validators'),
                    ('checker', 'output_validators'),
                ]:
                src = getattr(details, name)
                # TODO handle the case where src is not Python.
                # We need to compile it and "pass the compiled file" somehow.
                srcf = os.path.join(problem_loc, 'kgkompiled', 'pc2', os.path.basename(src.filename)) 
                rel_targf = os.path.join(code, targ, os.path.basename(src.filename))
                targf = os.path.join(cdp_config, rel_targf)
                touch_container(targf)
                copyfile(srcf, targf)
                problem_env[letter][name] = os.path.join(target_cdp_config, rel_targf)

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

        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing contest config files')
        for file in ['contest.yaml', 'problemset.yaml']:
            info_print('Writing', file)
            source = os.path.join(contest_template, file)
            target = os.path.join(cdp_config, file)
            touch_container(target)
            with open(source) as source_f, open(target, 'w') as target_f:
                target_f.write(source_f.read().format(**env))

        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing problem files')
        for letter in letters:
            penv = dict(env)
            penv.update(problem_env[letter])
            code = penv['problem_code']
            for file in ['problem.yaml', os.path.join('problem_statement', 'problem.tex')]:
                info_print('Writing', file, 'for', code)
                source = os.path.join(contest_template, os.path.basename(file))
                target = os.path.join(cdp_config, code, file)
                touch_container(target)
                with open(source) as source_f, open(target, 'w') as target_f:
                    target_f.write(source_f.read().format(**penv))

            info_print("Copying model solution")
            source = penv['details'].model_solution.rel_filename
            target = os.path.join(cdp_config, code, 'submissions', 'accepted', os.path.basename(source))
            touch_container(target)

            copyfile(source, target)

            info_print(f"Copying data for {code}...")
            try:
                src_format = KGFormat(penv['problem_loc'], read='io')
            except FormatError as exc:
                raise CommandError(f"No tests found for '{penv['problem_loc']}'. Please run 'kg make all' "
                        "to generate the files, or call 'kg kontest' with the '-m' option.") from exc
            for data_loc in [
                    os.path.join(cdp_config, code, 'data', 'secret'),
                    os.path.join(ext_data, code),
                ]:
                info_print("Copying to", data_loc)
                dest_format = KGFormat(write='io', tests_folder=data_loc)
                copied = 0
                for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
                    touch_container(dsti)
                    touch_container(dsto)
                    copyfile(srci, dsti)
                    copyfile(srco, dsto)
                    copied += 2
                succ_print("Copied", copied, "files")

    decor_print()
    decor_print('-'*42)
    beginfo_print('Making passwords')
    write_passwords_format(contest, args.format, seedval=seedval, dest=contest_folder)
    succ_print('Done passwords')

    if not args.no_seating and contest.seating:
        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing seating arrangement')
        write_seating(contest, seedval=seedval, dest=contest_folder)





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
