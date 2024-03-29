from collections import defaultdict, OrderedDict, Counter
from contextlib import ExitStack
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

                    - (for problems) [*[kg init]*], [*[kg make]*], [*[kg gen]*], [*[kg test]*], [*[kg run]*], [*[kg compile]*]
                    - (for contests) [*[kg contest]*]

                See the individual --help texts for each command, e.g., [*[kg init --help]*].
        ''')))
parser.add_argument('--krazy', action='store_true', help="Go krazy. (Don't use unless drunk)")
# TODO add 'verbose' option here
subparsers = parser.add_subparsers(
        help='which operation to perform',
        dest='main_command',
        metavar='{konvert,konvert-sequence,subtasks,gen,test,run,make,joke,init,kompile,kontest,seating,passwords}')
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

    copied_i = []
    copied_o = []
    info_print("Copying now...")
    for (srci, srco), (dsti, dsto) in zip(src_format.thru_io(), dest_format.thru_expected_io()):
        copy_file(srci, dsti)
        copy_file(srco, dsto)
        copied_i.append(dsti)
        copied_o.append(dsto)
    succ_print("Copied", len(copied_i) + len(copied_o), "files")
    return copied_i, copied_o





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
subtasks_p.add_argument('-w', '--max-workers', type=int, help=
        'number of workers to perform the task '
        "(default is based on Python's default behavior according to "
        "https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor "
        "which is min(32, os.cpu_count() + 4) as of Python 3.8)")
# TODO support "compiler through validator"

@set_handler(subtasks_p)
def kg_subtasks(format_, args):
    if not args.format: args.format = format_
    format_ = get_format(args, read='i')
    details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    subtasks = args.subtasks or list(map(str, details.valid_subtasks))
    detector = _get_subtask_detector_from_args(args, purpose='subtask computation', details=details)

    compute_subtasks(subtasks, detector, format=format_, include_subtask_groups=True, max_workers=args.max_workers)

def _get_subtask_detector_from_args(args, *, purpose, details=None):
    if details is None:
        details = Details.from_format_loc(args.format, args.details, relpath=args.loc)

    # build detector
    detector = Program.from_args(args.file, args.command)
    if not detector: # try validator
        detector = detector_from_validator(Program.from_args(args.validator_file, args.validator_command))
    
    # try detector from details
    if not detector: detector = details.subtask_detector
    
    # can't build any detector!
    if not detector: raise CommandError(f"Missing detector/validator (for {purpose})")

    # find subtask list
    from_validator = detector.filename in {'!detector_from_validator', '!detector_through_validator'}
    if from_validator and not args.subtasks: # subtask list required for detectors from validator
        raise CommandError(f"Missing subtask list (for {purpose})")

    return detector

def _collect_subtasks(input_subs):
    @wraps(input_subs)
    def _input_subs(subtasks, *args, **kwargs):
        subtset = set(subtasks)
        include_subtask_groups = kwargs.pop('include_subtask_groups', True)

        # iterate through inputs, run our detector against them
        subtasks_of = OrderedDict()
        all_subtasks = set()
        files_of_subtask = {sub: set() for sub in subtset}
        subtask_groups = {}
        for input_, subs in input_subs(subtasks, *args, **kwargs):
            subtasks_of[input_] = set(subs)
            if not subtasks_of[input_]:
                raise CommandError(f"No subtasks found for {input_}")
            if subtset and not (subtasks_of[input_] <= subtset):
                raise CommandError("Found invalid subtasks! "
                    + ' '.join(map(repr, natsorted(subtasks_of[input_] - subtset))))
            all_subtasks |= subtasks_of[input_]
            for sub in subtasks_of[input_]: files_of_subtask[sub].add(input_)
            info_print(f"Subtasks found for {input_}:", end=' ')
            key_print(*natsorted(subtasks_of[input_]))
            subtask_groups[' '.join(natsorted(subtasks_of[input_]))] = set(subtasks_of[input_])

        info_print("Distinct subtasks found:", end=' ')
        key_print(*natsorted(all_subtasks))

        if subtset:
            assert all_subtasks <= subtset
            if all_subtasks != subtset:
                warn_print('Warning: Some subtasks not found:', *natsorted(subtset - all_subtasks), file=stderr)

        info_print()
        info_print("Subtask dependencies:")
        depends_on = {sub: {sub} for sub in subtset}
        for sub in natsorted(subtset):
            if files_of_subtask[sub]:
                deps = [dep for dep in natsorted(subtset) if dep != sub and files_of_subtask[dep] <= files_of_subtask[sub]]
                print(info_text("Subtask"), key_text(str(sub).rjust(2)), info_text("contains the ff subtasks:"), key_text(*deps))
                for dep in deps: depends_on[dep].add(sub)
        
        if include_subtask_groups:
            representing = {}
            represented_by = {}
            for sub in natsorted(all_subtasks):
                candidates = {key: group for key, group in subtask_groups.items() if sub in group and group <= depends_on[sub]}
                if candidates:
                    try:
                        group_key = next(key
                            for key, group in candidates.items()
                            if all(other <= group for other in candidates.values()))
                        if group_key in represented_by:
                            del representing[represented_by[group_key]]
                        representing[sub] = group_key
                        represented_by[group_key] = sub
                    except StopIteration:
                        pass

            raw_group_str = {group: f"{{{group}}}" for group in subtask_groups}
            mxl = max(map(len, raw_group_str.values()))
            def group_str(group):
                group_s = raw_group_str[group].rjust(mxl)
                if group in represented_by:
                    return key_text(group_s), info_text("AKA subtask"), key_text(str(represented_by[group]).rjust(2))
                else:
                    return key_text(group_s),

            info_print()
            info_print("Subtask groups:")
            for group_key in natsorted(subtask_groups):
                print(*group_str(group_key))

            info_print()
            info_print("Subtask group representations:")
            for sub in natsorted(all_subtasks):
                if sub in representing:
                    print(info_text("Subtask"), key_text(str(sub).rjust(2)), info_text("is represented by subtask group:"),
                          *group_str(representing[sub]))
                else:
                    warn_print('Warning: No subtask group represents subtask', sub, file=stderr)

            info_print()
            info_print("Subtask group dependencies:")
            for key, group in natsorted(subtask_groups.items()):
                deps = [depkey for depkey, dep in natsorted(subtask_groups.items()) if dep != group and group < dep]
                print(*group_str(key), info_text("contains the ff subtask groups:"))
                for depkey in deps: print(*group_str(depkey))
                info_print()
        
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
def compute_subtasks(subtasks, detector, *, format=None, relpath=None, max_workers=None):
    subtset = set(subtasks)

    # iterate through inputs, run our detector against them
    detector.do_compile()

    def produce(index, input_):
        with open(input_) as f:
            try:
                res = detector.do_run(*subtasks, stdin=f, stdout=PIPE, check=True, label='SUBTASK_DETECTOR')
            except CalledProcessError as cpe:
                err_print(f"The detector raised an error for {input_}", file=stderr)
                raise CommandError(f"The detector raised an error for {input_}") from cpe
        return input_, set(res.result.stdout.decode('utf-8').split())

    return thread_pool_executor(
            "Computing subtasks",
            max_workers=max_workers,
            thread_name_prefix="kg_compute_subtasks",
        ).map(produce, *zip(*enumerate(format.thru_inputs())))





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
gen_p.add_argument('-w', '--max-workers', type=int, help=
        'number of workers to perform the task '
        "(default is based on Python's default behavior according to "
        "https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor "
        "which is min(32, os.cpu_count() + 4) as of Python 3.8)")

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

    interacts = judge_data_maker.attributes.get('interacts') or details.interactor and model_solution == judge_data_maker
    judge = Program.from_args(args.judge_file, args.judge_command) or details.checker

    if not judge: raise CommandError("Missing judge")

    generate_outputs(format_, judge_data_maker, model_solution=model_solution, interacts=interacts,
            judge=judge, interactor=details.interactor, node_count=details.node_count, max_workers=args.max_workers)

def generate_outputs(format_, data_maker, *, model_solution=None, judge=None, interacts=False, interactor=None, node_count=None, max_workers=None):
    if not data_maker: raise CommandError("Missing solution/data maker")
    data_maker.do_compile()
    if judge: judge.do_compile()
    if model_solution and model_solution != data_maker: model_solution.do_compile()
    if interactor: interactor.do_compile()
    data_maker_name = 'model_solution' if model_solution == data_maker else 'data_maker'
    interaction_mode = IMode.FIFO if node_count is not None and node_count > 1 else IMode.STDIO

    def produce(index, input_, output_):
        def pref(print, *args, **kwargs):
            info_print(f"[{index}]".rjust(5), end=' ')
            print(*args, **kwargs)
        touch_container(output_)
        pref(print, info_text('GENERATING'), src_text(input_, '-->', output_))
        try:
            if interacts:
                if not interactor:
                    raise CommandError('"interacts" is true but no interactor found')
                data_maker.do_interact(interactor, time=True, label='DATA_MAKER_{id}', check=True,
                        node_count=node_count,
                        interaction_mode=interaction_mode,
                        pass_id=interaction_mode == IMode.FIFO,
                        interactor_args=[input_, output_],
                        interactor_kwargs=dict(time=True, label='INTERACTOR', check=True),
                    )
            else:
                with open(input_) as inp, open(output_, 'w') as outp:
                    data_maker.do_run(stdin=inp, stdout=outp, time=True, label='DATA_MAKER', check=True)
        except InteractorException as ie:
            pref(err_print, f"The interactor raised an error with the {data_maker_name} for {input_}", file=stderr)
            raise CommandError(f"The interactor raised an error with the {data_maker_name} for {input_}") from ie
        except SubprocessError as se:
            pref(err_print, f"The {data_maker_name} raised an error for {input_}", file=stderr)
            raise CommandError(f"The {data_maker_name} raised an error for {input_}") from se

        if judge and model_solution:
            @contextlib.contextmanager  # so that the file isn't closed
            def model_output():
                if model_solution == data_maker:
                    yield output_
                else:
                    with tempfile.NamedTemporaryFile(delete=False, prefix=f'kg_tmp_out_{index:>03}_') as tmp:
                        pref(info_print, f"  Running model solution on {input_}")
                        try:
                            if interactor:
                                model_solution.do_interact(interactor,
                                        label='MODEL_SOLUTION_{id}', check=True,
                                        node_count=node_count,
                                        interaction_mode=interaction_mode,
                                        pass_id=interaction_mode == IMode.FIFO,
                                        interactor_args=[input_, tmp.name],
                                        interactor_kwargs=dict(label='INTERACTOR', check=True),
                                    )
                            else:
                                with open(input_) as inp:
                                    model_solution.do_run(stdin=inp, stdout=tmp, label='MODEL_SOLUTION', check=True)
                        except InteractorException as ie:
                            pref(err_print, f"The interactor raised an error with the model_solution for {input_}", file=stderr)
                            raise CommandError(f"The interactor raised an error with the model_solution for {input_}") from ie
                        except SubprocessError as se:
                            pref(err_print, f"The interaction raised an error for {input_}", file=stderr)
                            raise CommandError(f"The interaction raised an error for {input_}") from se
                        yield tmp.name
            with model_output() as model_out:
                try:
                    judge.do_run(*map(os.path.abspath, (input_, model_out, output_)), check=True, label='CHECKER')
                except CalledProcessError as cpe:
                    pref(err_print, f"The judge did not accept {output_}", file=stderr)
                    raise CommandError(f"The judge did not accept {output_}") from cpe

        pref(print, info_text('GENERATED ', input_, '-->'), key_text(output_))
        if max_workers == 1: print()

    with thread_pool_executor(
                "Generating output files",
                max_workers=max_workers,
                thread_name_prefix="kg_gen_output_files",
            ) as executor:
        wait_all(
                (executor.submit(produce, index, input_, output_) for index, (input_, output_) in enumerate(format_.thru_io())),
                "generate files",
                executor=executor,
                logf=stderr)





##########################################
# test against output data

test_p = subparsers.add_parser('test',
    formatter_class=argparse.RawDescriptionHelpFormatter,
               help='Test a program against given input and output files',
        description=cformat_text(dedent('''\
                Test a program against given input and output files.

                $ [*[kg test -i [input_pattern] -o [output_pattern] -f [solution_program]]*]

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


                If you wrote your problem using "kg init", then you may omit "-i", "-o", "-f" and "-jf"; they will
                default to the KompGen format ("tests/*.in" and "tests/*.ans"), and other details will be parsed
                from details.json, so for example, "[*[kg test]*]" without options would just work. (You can still pass
                them of course.)


                If your command (-c or -jc) requires leading dashes, then the argument parser might interpret
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
test_p.add_argument('-n', '--node-count', type=int, help="The number of nodes that the solution will be run on. If this "
                                                         "is given, there must also be an interactor.")

# I didn't put workers and Threads here for more accurate timing. TODO reconsider if 'num_cores - 1' threads is ok or something
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

    node_count = args.node_count
    if node_count is None: node_count = details.node_count
    if node_count is None:
        node_count = 1
        interaction_mode = IMode.STDIO
    else:
        if not interactor: raise CommandError("There must be an interactor if node-count is given")
        interaction_mode = IMode.FIFO

    interactor_strict_args = interactor and not interactor.filename.endswith('.py') # this is hacky for now...
    judge_strict_args = args.judge_strict_args
    # *_strict_args should probably be subsumed by arg formatting in details.json?
    # anyway, default behavior: use -C -t -v if ends in .py, else no extras
    solution.do_compile()
    judge.do_compile()
    if interactor: interactor.do_compile()
    scoresheet = {}
    for index, (input_, output_) in enumerate(format_.thru_io()):
        def get_score():
            nonlocal interactor_strict_args, judge_strict_args
            with ExitStack() as estack:
                tmp = estack.enter_context(tempfile.NamedTemporaryFile(delete=False, prefix=f'kg_tmp_out_{index:>03}_'))
                result_tmp = estack.enter_context(tempfile.NamedTemporaryFile(delete=False, prefix=f'kg_tmp_res_{index:>03}_'))
                if interactor and not interactor_strict_args:
                    dummy_tmp = estack.enter_context(tempfile.NamedTemporaryFile(delete=False, prefix=f'kg_tmp_dmy_{index:>03}_'))
                info_print("\nFile", str(index).rjust(3), 'CHECKING AGAINST', input_)
                solutions_res = None
                interactor_res = None
                try:
                    if interactor:
                        iargs = [input_, tmp.name]
                        if not interactor_strict_args:
                            iargs += [dummy_tmp.name, result_tmp.name, '-C', solution.filename, '-t', str(index), '-v']
                        solutions_res, interactor_res = solution.do_interact(
                                interactor,
                                time=True,
                                label='SOLUTION_{id}',
                                check=True,
                                log_exc=False,
                                interaction_mode=interaction_mode,
                                pass_id=interaction_mode == IMode.FIFO,
                                node_count=node_count,
                                interactor_args=iargs,
                                interactor_kwargs=dict(check=False),
                                time_limit=time_limit,
                            )
                    else:
                        assert node_count == 1
                        with open(input_) as inp:
                            solutions_res = [solution.do_run(
                                    stdin=inp,
                                    stdout=tmp,
                                    time=True,
                                    label='SOLUTION',
                                    check=True,
                                    log_exc=False,
                                    time_limit=time_limit,
                                )]
                except TimeoutExpired as exc:
                    err_print('The solution took too long, so it was force-terminated...')
                    err_print(exc)
                    return False, 0
                except CalledProcessError as exc:
                    err_print('The solution issued a runtime error...')
                    err_print(exc)
                    return False, 0
                finally:
                    get_score.running_time = None
                    if solutions_res:
                        runtimes = [sres.running_time for sres in solutions_res if sres.running_time is not None]
                        if runtimes: get_score.running_time = sum(runtimes), max(runtimes)

                # Check if the interactor issues WA by itself. Don't invoke the judge
                if interactor_res and getattr(interactor_res.result, 'returncode', 0):
                    err_print('The interactor did not accept the interaction...')
                    return False, 0

                def run_judge():
                    jargs = list(map(os.path.abspath, (input_, tmp.name, output_)))
                    if not judge_strict_args:
                        jargs += [result_tmp.name, '-C', solution.filename, '-t', str(index), '-v']
                    return judge.do_run(*jargs, check=False).result.returncode

                info_print("Checking the output...")
                returncode = run_judge()
                if returncode == 3 and not judge_strict_args: # try again but assume the judge is strict
                    info_print(
                        "The error above might just be because of testlib... "
                        "trying to judge again (but strict mode this time)"
                    )
                    judge_strict_args = True
                    returncode = run_judge()
                correct = returncode == 0

                try:
                    with open(result_tmp.name) as result_tmp_file:
                        score = json.load(result_tmp_file)['score']
                except Exception as exc:
                    score = 1 if correct else 0 # can't read score. use binary scoring

                if get_score.running_time is None:
                    warn_print("Warning: The running time cannot be extracted from this run.")
                else:
                    rt_sum, rt_max = get_score.running_time
                    if node_count == 1: assert rt_sum == rt_max
                    # TODO we're using rt_max since we're using wall-clock time (even naively via time.time)
                    # but we probably want to use sum of user times.
                    # https://cms.readthedocs.io/en/v1.4/Task%20types.html
                    if rt_max > time_limit:
                        err_print(f"The solution exceeded the time limit of {time_limit:.3f} sec;", end=' ')
                        if node_count == 1:
                            err_print(f"it didn't finish after {rt_max:.3f} sec...")
                        else:
                            err_print(f"the total running time is {rt_sum:.3f} sec (max {rt_max:.3f} sec)...")
                        if score > 0: info_print(f"It would have gotten a score of {score} otherwise...")
                        return False, 0

                return correct, score

        correct, score = get_score()
        scoresheet[index] = {
            'input': input_,
            'correct': correct,
            'score': score,
            'running_time': get_score.running_time,
        }
        if correct:
            succ_print("File", str(index).rjust(3), 'correct')
        else:
            err_print("File", str(index).rjust(3), 'WRONG' + '!'*11)
        if not 0 <= score <= 1:
            warn_print(f"Warning: The score '{score}' is invalid; it must be in the interval [0, 1].")

    def abbreviate_indices(indices):
        if not indices: return 'none'
        return compress_t_sequence(','.join(map(str, sorted(indices))))

    def print_file_list(description, indices):
        if indices:
            info_print(f"{len(indices):3} file(s) {description}:", abbreviate_indices(indices))
        else:
            info_print(f"{len(indices):3} file(s) {description}")


    def write_raw_summary():
        """ print the raw files gotten correct and wrong """
        corrects = [index for index, score_row in sorted(scoresheet.items()) if score_row['correct']]
        wrongs = [index for index, score_row in sorted(scoresheet.items()) if not score_row['correct']]
        running_times = [*filter(None, (score_row['running_time'] for score_row in scoresheet.values()))]
        max_time = max(rt_max for rt_sum, rt_max in running_times) if running_times else None
        decor_print()
        decor_print('.'*42)
        beginfo_print('SUMMARY:')
        print_file_list('gotten correct', corrects)
        print_file_list('gotten wrong  ', wrongs)
        (succ_print if len(corrects) == len(scoresheet) else err_print)(len(corrects), end=' ')
        (succ_print if len(corrects) == len(scoresheet) else info_print)(f'out of {len(scoresheet)} files correct')
        if max_time is None:
            info_print('No running time was found from any run')
        else:
            info_print(f'Max running time: {max_time:.2f}sec.')
        decor_print('.'*42)

    @memoize
    def get_all_subtask_details():
        print()
        info_print('Obtaining subtask info...')
        subtasks = args.subtasks or list(map(str, details.valid_subtasks))
        if os.path.isfile(details.subtasks_files):
            inputs = [score_row['input'] for index, score_row in sorted(scoresheet.items())]
            subtasks_of, all_subtasks = extract_subtasks(
                subtasks,
                details.load_subtasks_files(),
                inputs=inputs,
                include_subtask_groups=False,
            )
        else:
            detector = _get_subtask_detector_from_args(args, purpose='subtask scoring', details=details)
            subtasks_of, all_subtasks = compute_subtasks(
                subtasks,
                detector,
                format=format_,
                include_subtask_groups=False,
            )

        def get_max_score(sub):
            max_score = details.valid_subtasks[int(sub)].score if isinstance(details.valid_subtasks, dict) else 1
            if max_score is None: max_score = 1
            return max_score

        # normal grading
        all_subtasks = {sub: {
                'weight': get_max_score(sub),
                'indices': [],
                'scores': [],
                'running_times': [],
            } for sub in all_subtasks}
        for index, score_row in sorted(scoresheet.items()):
            for sub in subtasks_of[score_row['input']]:
                all_subtasks[sub]['indices'].append(index)
                all_subtasks[sub]['scores'].append(score_row['score'])
                all_subtasks[sub]['running_times'].append(score_row['running_time'])

        # compute scores per subtask using the per-subtask scoring policy
        for sub, sub_details in all_subtasks.items():
            if details.scoring_per_subtask == '!min':
                sub_details['score'] = min(score for score in sub_details['scores'])
            elif details.scoring_per_subtask == '!ave':
                sub_details['score'] = sum(sub_details['scores']) / len(sub_details['scores'])
            else:
                raise ValueError(f"Unknown/Unsupported per-subtask scoring policy: {details.scoring_per_subtask}")

            sub_details['weighted_score'] = sub_details['weight'] * sub_details['score']
            running_times = [*filter(None, sub_details['running_times'])] if sub_details['running_times'] else None
            sub_details['max_running_time'] = max(rt_max for rt_sum, rt_max in running_times) if running_times else None
        return all_subtasks

    def get_score_for(group_scores):
        if details.scoring_overall == '!sum':
            return sum(weight * score for weight, score in group_scores)
        if details.scoring_overall == '!ave':
            return sum(weight * score for weight, score in group_scores) / sum(weight for weight, score in group_scores)
        if details.scoring_overall == '!min':
            return min(weight * score for weight, score in group_scores)

        raise ValueError(f"Unknown/Unsupported overall scoring policy: {details.scoring_overall}")

    write_raw_summary()

    if format_.name and details.valid_subtasks:
        # groups are subtasks
        group_scores = [(sub_details['weight'], sub_details['score'])
            for sub, sub_details in natsorted(get_all_subtask_details().items())
        ]
    else:
        # groups are individual files
        group_scores = [(details.scoring_default_weight, score_row['score'])
            for index, score_row in sorted(scoresheet.items())
        ]

    scoring_result = get_score_for(group_scores)
    max_scoring_result = get_score_for([(weight, 1) for weight, score in group_scores])

    # print the subtask grades
    if format_.name and details.valid_subtasks:
        # print the raw summary again (because get_subtasks has huge output)
        write_raw_summary()
        beginfo_print('SUBTASK REPORT:')
        for sub, sub_details in natsorted(get_all_subtask_details().items()):
            score = sub_details['weighted_score']
            weight = sub_details['weight']
            max_running_time = sub_details['max_running_time']
            times = []
            print(
                info_text("Subtask ="),
                key_text(str(sub).rjust(4)),
                info_text(": Score = "),
                (
                    succ_text if score >= weight else
                    info_text if score > 0 else
                    err_text
                )(f"{score:8.3f}"),
                info_text(f" out of {weight:8.3f}"),
                (
                    info_text("  (no running time was found)")
                    if max_running_time is None else
                    info_text(f"  w/ max running time: {max_running_time:.2f}sec.")
                ), sep='')

            if not 0 <= score <= weight:
                warn_print(f"Warning: The score {score} is invalid: "
                           f"it must be in the interval [0, {weight}]")

    # print the overall score
    print()
    print(info_text("Total Score =",
          (succ_text if scoring_result >= max_scoring_result else
           info_text if scoring_result > 0 else
           err_text)(f"{scoring_result:8.3f}"),),
          info_text(f" out of {max_scoring_result:8.3f}"),
          sep='')
    info_print(f'using the scoring policy {details.logical_scoring}')

    print()
    info_print("You can clear temp files by running 'kg-aux clear-temp-files'")



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
                solution.do_run(stdin=inp, time=True, label='PROGRAM', check=True)
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
make_p.add_argument('-w', '--max-workers', type=int, help=
        'number of workers to perform the task '
        "(default is based on Python's default behavior according to "
        "https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor "
        "which is min(32, os.cpu_count() + 4) as of Python 3.8)")

@set_handler(make_p)
def _kg_make(format_, args):
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'make'.")

    details = Details.from_format_loc(format_, args.details, relpath=args.loc)
    kg_make(args.makes, args.loc, format_, details, validation=args.validation, checks=args.checks, max_workers=args.max_workers)

def kg_make(omakes, loc, format_, details, *, validation=False, checks=False, max_workers=None):
    makes = set(omakes)
    valid_makes = {'all', 'inputs', 'outputs', 'subtasks'}
    if not (makes <= valid_makes):
        raise CommandError(f"Unknown make param(s): {ctext(*sorted(makes - valid_makes))} (should be in {valid_makes})")

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

        filenames = [*run_testscript(
                fmt.thru_expected_inputs(),
                script,
                details.generators,
                relpath=loc,
                validator=details.validator if validation else None,
                max_workers=max_workers)]

        succ_print('DONE MAKING INPUTS.')

    if 'outputs' in makes:
        decor_print()
        decor_print('~~ '*14)
        beginfo_print('MAKING OUTPUTS...' + ("WITH CHECKS..." if checks else 'WITHOUT CHECKS'))
        fmt = get_format_from_type(format_, loc, read='i', write='o', clear='o')
        interacts = details.judge_data_maker.attributes.get('interacts') or details.interactor and details.model_solution == details.judge_data_maker
        generate_outputs(
                fmt, details.judge_data_maker,
                model_solution=details.model_solution,
                judge=details.checker if checks else None,
                interacts=interacts,
                node_count=details.node_count,
                interactor=details.interactor,
                max_workers=max_workers)

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
            if not detector:
                raise CommandError("Missing detector/validator")

            # find subtask list
            subtasks = list(map(str, details.valid_subtasks))
            if details.validator and not subtasks: # subtask list required for detectors from validator
                raise CommandError("Missing subtask list")

            # iterate through inputs, run our detector against them
            subtasks_of, all_subtasks = compute_subtasks(
                    subtasks, detector,
                    format=get_format_from_type(format_, loc, read='i'),
                    relpath=loc,
                    include_subtask_groups=True,
                    max_workers=max_workers)

            info_print(f'WRITING TO {details.subtasks_files}')
            details.dump_subtasks_files(construct_subs_files(subtasks_of))

            succ_print('DONE MAKING SUBTASKS.')

    print()
    info_print("You can clear temp files by running 'kg-aux clear-temp-files'")


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
    '5kg < 5kig',
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
                
                Include an interactor in the prepopulated files.
                $ [*[kg init my-problem --interactor]*]

                Set the time limit to 7sec. Can be changed later (in details.json)
                $ [*[kg init my-problem --time-limit 7]*]

                You can also combine options, e.g.,
                $ [*[kg init my-problem --subtasks 5 --minimal --checker --interactor -tl 7 -t "My Cool Problem"]*]
        ''')))

init_p.add_argument('problemcode', help='Problem code. Must not contain special characters.')
init_p.add_argument('-l', '--loc', default='.', help='where to make the problem')
init_p.add_argument('-t', '--title', help='Problem title. (Default is generated from problemcode)')
init_p.add_argument('-s', '--subtasks', type=int, default=0, help='Number of subtasks. (0 if binary)')
init_p.add_argument('-m', '--minimal', action='store_true', help="Only put the essentials.")
init_p.add_argument('-c', '--checker', action='store_true', help="Include a checker.")
init_p.add_argument('-i', '--interactor', action='store_true', help="Include an interactor.")
init_p.add_argument('-tl', '--time-limit', type=int, default=2, help='Time limit.')

# We disallow single-character names because some contest systems do so.
# But maybe we should allow it? I'm open for discussion. -Kevin
valid_problemcode = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z]\Z')

@set_handler(init_p)
def kg_init(format_, args):
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'init'.")
  
    prob = args.problemcode

    if not valid_problemcode.match(prob):
        raise CommandError("No special characters allowed for the problem code, "
                "and the first and last characters must be a letter or a digit.")

    src = os.path.join(kg_problem_template, 'kg')
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
        'interactor': args.interactor,
        'subtasks': args.subtasks,
        # Jinja's tojson doesn't seem to honor dict order, so let's just use json.dumps
        # TODO fix it using https://stackoverflow.com/questions/67214142/why-does-jinja2-filter-tojson-sort-keys (maybe...)
        "subtask_list": [OrderedDict(id=index, score=10) for index in range(1, args.subtasks + 1)],
        # TODO find a way to indent only up to a certain level
        'subtask_list_json': "[" + ','.join('\n    ' + json.dumps(sub) for sub in subtask_list) + "\n]",
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
                write will be compatible with the contest system/judge you are using.

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
                                'kg module.)')
compile_p.add_argument('-C', '--compress', action='store_true',
                                help='compress the program by actually compressing it. Use at your own risk.')
compile_p.add_argument('-w', '--max-workers', type=int, help=
        'number of workers to perform the task '
        "(default is based on Python's default behavior according to "
        "https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor "
        "which is min(32, os.cpu_count() + 4) as of Python 3.8)")

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
        max_workers=args.max_workers,
        )

def _get_cms_code(details, code_raw):
    return details.cms_options.get('name', ''.join(re.split(r'[._-]', code_raw)))

def kg_compile(format_, details, *target_formats, loc='.', shift_left=False, compress=False, python3='python3',
        dest_loc=None, files=[], extra_files=[], statement_file=None, global_statement_file=None, max_workers=None):

    valid_formats = {'hr', 'pg', 'pc2', 'dom', 'cms', 'cms-it'}
    if not set(target_formats) <= valid_formats:
        raise CommandError(f"Invalid formats: {set(target_formats) - valid_formats}")
    if not is_same_format(format_, 'kg'):
        raise CommandError(f"You can't use '{format_}' format to 'kompile'.")

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
    def load_module(module_id):
        if module_id not in locations:
            raise CommandError(f"Couldn't find module {module_id}! "
                    f"(Add it to {'other_programs' if problem_code else '--extra-files'}?)")

        with open(locations[module_id]) as f:
            @listify
            def lines():
                for line in f:
                    if not line.endswith('\n'):
                        warn_print('Warning:', locations[module_id], "doesn't end with a new line.")
                    yield line.rstrip('\n')

            return lines(), {
                'location': locations[module_id],
                'label': os.path.basename(locations[module_id]),
            }

    def get_module_id(module, context):
        nmodule = module
        if nmodule.startswith('.') and context['module_id'] in kg_libs:
            smodule = context['module_id'].split('.')
            while nmodule.startswith('.'):
                nmodule = nmodule[1:]
                smodule.pop()
            nmodule = '.'.join([*smodule, nmodule])


        if nmodule.startswith('.'):
            warn_print(f"Warning: Ignoring relative import for {module}", file=stderr)
            nmodule = nmodule.lstrip('.')

        return nmodule

    # get the statement file
    statement_file = (
        statement_file or details.statement_compiled or global_statement_file or
        details.statement_base or os.path.join(kg_problem_template, 'statement.pdf')
        # the last one is a dummy statement file...because some platforms require a statement file
    )


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
    # TODO do some kind of os.walk here and automatically detect these
    # importable_locations = [
    #     'formatters',
    #     'generators',
    #     'validators',
    #     'interactors',
    #     'checkers',
    #     'utils',
    #     'graphs',
    #     'grids',
    #     'math',
    # ]
    locations = {
        'kg.formatters': 'formatters.py',
        'kg.generators': 'generators.py',
        'kg.validators': 'validators.py',
        'kg.interactors': 'interactors.py',
        'kg.checkers': 'checkers.py',
        'kg.utils': os.path.join('utils', '__init__.py'),
        'kg.utils.hr': os.path.join('utils', 'hr.py'),
        'kg.utils.utils': os.path.join('utils', 'utils.py'),
        'kg.utils.judging': os.path.join('utils', 'judging.py'),
        'kg.utils.parsers': os.path.join('utils', 'parsers.py'),
        'kg.utils.streams': os.path.join('utils', 'streams.py'),
        'kg.utils.intervals': os.path.join('utils', 'intervals.py'),
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
    interactors = []

    # detect checkers an interactors (try to be smart)
    for file in files:
        base, ext = os.path.splitext(os.path.basename(file.rel_filename))
        if 'checker' in base and ext == '.py':
            checkers.append(file)
        if 'interactor' in base and ext == '.py':
            interactors.append(file)

    if problem_code:
        # current files
        checkers.insert(0, details.checker)
        interactors.insert(0, details.interactor)

        all_local = [details.validator, details.model_solution] + (
                details.generators + details.other_programs + files + extra_files + checkers + interactors)

        # files that start with 'grader.' (for cms mainly)
        graders = [file for file in details.other_programs if os.path.basename(file.filename).startswith('grader.')]

        cms_attachments = [os.path.join(loc, attachment) for attachment in details.cms_options.get('attachments', [])]

        # files that need to be either translated (kg python codes) or just copied (everything else)
        to_compiles = {
            'pg': [details.validator] + checkers + interactors + details.generators,
            'hr': checkers,
            'pc2': [details.validator] + checkers, # TODO interactors
            'dom': [details.validator] + checkers, # TODO interactors
            'cms': [(checker,    "checker" if i == 1 else f"checker{i}")    for i, checker    in enumerate(checkers, 1)]
                 + [(interactor, "manager" if i == 1 else f"interactor{i}") for i, interactor in enumerate(interactors, 1)]
                 + graders,
            'cms-it': [(checker, os.path.join("check", "checker")) for checker in checkers]
                    + [(grader,  os.path.join("sol", os.path.basename(grader.rel_filename))) for grader in graders],
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
            default = 1 # hardcoded for now
            warn_print(f'Warning: no score value found for subtask {sub}... using the default {default} point(s)')
            subtask_score.missing = True
            return default
    subtask_score.missing = False

    # convert to various formats
    for fmt, name, copy_files, shebang_format in [
            ('pg', 'Polygon', True, None),
            ('hr', 'HackerRank', True, None),
            ('pc2', 'PC2', False, None),
            ('dom', 'DOMjudge', False, "#!/chroot/domjudge/usr/bin/{}"),
            ('cms', 'CMS', True, None),
            ('cms-it', 'CMS Italian', False, None),
        ]:
        if fmt not in target_formats: continue
        to_compile = files + to_compiles.get(fmt, [])

        shebang_format = shebang_format or "#!/usr/bin/env {}"

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

        if fmt == 'cms':
            for attachment in cms_attachments:
                to_copy[attachment] = os.path.join('attachments', os.path.basename(attachment))

        if fmt in {'cms-it', 'cms'} and problem_code:
            cms_code = _get_cms_code(details, problem_code)
            if cms_code != problem_code:
                info_print(f"Using the code name {cms_code!r} instead of {problem_code!r}.")
                if 'name' not in details.cms_options:
                    warn_print(f"Warning: Using {cms_code!r} instead of {problem_code!r}. "
                                "(CMS problem code names should contain only letters and digits)")

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
            copy_file(filename, target)

        # translating
        for filename in natsorted(to_translate):
            module = get_module(filename)
            info_print(f'[{module}] converting {filename} to {targets[module]} (kompiling)')
            touch_container(targets[module])
            lines, add_context = load_module(module)
            lines = list(compile_lines(lines,
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
                    **add_context,
                ))
            with open(targets[module], 'w') as f:
                shebanged = False
                for line in lines:
                    assert not line.endswith('\n')
                    if not shebanged and not line.startswith('#!'):
                        shebang_line = shebang_format.format(python3)
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
                    lines, add_context = load_module(module)
                    lines = list(compile_lines(lines,
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
                            **add_context,
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
                    lines, add_context = load_module(module)
                    lines = list(compile_lines(lines,
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
                            **add_context,
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

            lines = list(transpile_testscript_pg(script, details.generators, relpath=loc, max_workers=max_workers))

            with open(target, 'w') as f:
                for line in lines:
                    assert not line.endswith('\n')
                    print(line, file=f)

        # copy over the files
        if copy_files and problem_code:
            info_print('copying test data from', loc, 'to', dest_folder, '...')
            # TODO code this better.
            if fmt == 'cms':
                input_files, output_files = convert_formats(
                        (format_, loc),
                        (fmt, dest_folder),
                        dest_kwargs=dict(subtasks=subtasks_files, **details.cms_options)
                    )
            else:
                input_files, output_files = convert_formats(
                        (format_, loc),
                        (fmt, dest_folder),
                    )


        if fmt == 'dom' and problem_code:
            # statement file
            info_print('creating statement file...')
            source_file = statement_file
            target_file = os.path.join(dest_folder, 'statement.pdf')
            copy_file(source_file, target_file)

        # do special things for cms
        if fmt == 'cms-it' and problem_code:

            # statement file (required)
            info_print('creating statement file...')
            source_file = statement_file
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
                    problem_code=cms_code,
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
            # copy statement file
            source_file = statement_file
            target_file = os.path.join(dest_folder, 'statement.pdf')
            info_print(f'creating statement file... (from {source_file})')
            copy_file(source_file, target_file)

            # make test codes
            def test_code_from_input(inputf):
                base, ext = os.path.splitext(os.path.basename(inputf))
                return base
            test_codes = [test_code_from_input(inputf) for inputf in input_files]

            # create config file
            config = {
                'name': cms_code,
                'title': details.title,
                'time_limit': details.time_limit,
                # only Batch, Communication and OutputOnly.
                # For OutputOnly, just override with cms_options.
                'task_type': details.cms_options.get('task_type', 'Communication' if details.interactor else 'Batch'),
                'codenames': test_codes,
                'statement': 'statement.pdf',
            }

            if config['task_type'] == 'Communication':
                node_count = details.node_count
                if node_count is None: node_count = 1
                if node_count < 1:
                    raise CommandError(f"Node count invalid: {node_count}")
                config['node_count'] = node_count
                config['io_type'] = 'std_io'  # refers to the user's way of getting I/O, not the manager's

            scoring_overall = details.scoring_overall
            if details.binary:
                if scoring_overall == '!min':
                    # this is just like a problem with a single subtask
                    config['score_type'] = 'GroupMin'
                    config['score_type_parameters'] = [[details.scoring_default_weight, '.*']]
                    total_score = sum(score for score, *rest in config['score_type_parameters'])
                elif scoring_overall == '!sum':
                    # this is just like a problem with a separate subtask per file
                    def input_base_regex(input_file):
                        base, ext = os.path.splitext(os.path.basename(input_file))
                        if ext != '.in': raise CommandError(f"Expected input file extension '.in', got {ext}")
                        return re.escape(base)
                    config['score_type'] = 'GroupMin'
                    config['score_type_parameters'] = [[
                        details.scoring_default_weight, input_base_regex(input_file),
                        ] for input_file in input_files
                    ]
                    total_score = sum(score for score, *rest in config['score_type_parameters'])
                elif scoring_overall == '!ave':
                    # this is just like !sum, but we can hardcode the score_type_parameters to 100/len(tests).
                    # The docs say 'score_type_parameters' should be an int, but that's a lie.
                    config['score_type'] = 'Sum'
                    config['score_type_parameters'] = 100 / len(input_files)
                    total_score = config['score_type_parameters'] * len(input_files)
                else:
                    raise CommandError(
                        f"Unsupported scoring policy {scoring_overall} for binary task")
            else:
                if scoring_overall != '!sum':
                    warn_print(
                        f"WARNING: Unsupported scoring policy {scoring_overall} for "
                        "task with subtasks, defaulting to !sum")
                    scoring_overall = '!sum'

                if scoring_overall == '!sum':
                    config['score_type'] = 'GroupMin'
                    # special-case OutputOnly
                    if config['task_type'] == 'OutputOnly':
                        files_in_subtask = {sub: [] for sub in details.valid_subtasks}
                        for low, high, subs in subtasks_files:
                            for idx in range(low, high + 1):
                                for sub in subs:
                                    files_in_subtask[sub].append(test_codes[idx])
                        config['score_type_parameters'] = [
                            [subtask_score(sub), '|'.join(files_in_subtask[sub])]
                            for sub in details.valid_subtasks
                        ]
                    else:
                        config['score_type_parameters'] = [
                            [subtask_score(sub), rf".+_subs.*_{sub}_.*"]
                            for sub in details.valid_subtasks
                        ]
                    total_score = sum(score for score, *rest in config['score_type_parameters'])
                else:
                    raise CommandError(
                        f"Unsupported scoring policy {scoring_overall} for task with "
                        "subtasks")

            if total_score == 100:
                info_print('The total score is', total_score)
            else:
                warn_print(f'WARNING: The total score is {total_score}, but we usually want 100')

            # override options
            config.update(details.cms_options)

            # make attachments 'basename'
            if 'attachments' in config:
                config['attachments'] = [os.path.basename(attachment) for attachment in config['attachments']]

            # write config file
            config_file = os.path.join(dest_folder, 'kg_cms_task.json')
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
                for inp, outp in CMSFormat(dest_folder, read='io', **config).thru_io():
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
    passwords, accounts = write_passwords_format(contest, args.format, seedval=seedval, dest=contest_folder)
    succ_print('Done passwords')

    contest_template = os.path.join(kg_contest_template, args.format)

    if args.format == 'cms-it' or args.format == 'cms':

        # identify key folders
        contest_data_folder = os.path.join(contest_folder, 'contest')

        # construct template environment
        env = {
            "datetime_created": datetime.now(),
            "contest": contest,
            "passwords": passwords,
        }

        # problem envs
        found_codes = {}
        codes = []
        problem_details = []
        for letter, problem_loc in zip(problem_letters(), contest.rel_problems):
            details = Details.from_format_loc(format_, os.path.join(problem_loc, 'details.json'), relpath=problem_loc)

            code_raw = os.path.basename(problem_loc)
            code = _get_cms_code(details, code_raw)
            if code in found_codes:
                found_codes[code] += 1
                code += str(found_codes[code])
            else:
                found_codes[code] = 1
            codes.append(code)
            problem_details.append(details)
            decor_print()
            decor_print('-'*42)
            print(beginfo_text("Getting problem"), key_text(repr(code_raw)), beginfo_text(f"(from {problem_loc})"))
            if code != code_raw:
                info_print(f"Using the code name {code!r} instead of {code_raw!r}.")
                if 'name' not in details.cms_options:
                    warn_print(f"Warning: Using {code!r} instead of {code_raw!r}. "
                                "(CMS problem code names should contain only letters and digits)")

            if args.make_all:
                info_print('Running "kg make all"...')
                kg_make(['all'], problem_loc, format_, details)

            info_print('Running "kg kompile"...')
            def dest_loc(loc, fmt):
                return os.path.join(contest_data_folder, code)

            kg_compile(format_, details, args.format,
                    loc=problem_loc,
                    dest_loc=dest_loc,
                    global_statement_file=contest.rel_global_statements,
                    python3=contest.python3_command)

    # cms-it specific stuff
    if args.format == 'cms-it':
        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing contest config files')
        info_print(f'Writing contest.yaml')
        source = os.path.join(contest_template, 'contest.yaml.j2')
        target = os.path.join(contest_data_folder, 'contest.yaml')
        kg_render_template_to(source, target, **env)
        
    if args.format == 'cms':

        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing contest config files')
        # write config
        config_file = os.path.join(contest_data_folder, 'kg_cms_contest.json')
        warn_print(
            "Note: For CMS, we're ignoring compilation and run options of languages. "
            "We're only taking the names.")
        config = {
            "description": contest.title,
            "name": contest.code,
            "problems": codes,
            "start": contest.start_time.timestamp(),
            "stop": contest.end_time.timestamp(),
            "per_user_time": contest.duration.total_seconds(),
            "timezone": contest.display_timezone,
            "languages": [lang['lang'] for lang in contest.langs],
            # compute score precision based on the individual problems' score precision
            "score_precision": max(problem.cms_options.get('score_precision', 0) for problem in problem_details),
        }
        info_print('writing config file...', config_file)
        with open(config_file, 'w') as fl:
            json.dump(config, fl, indent=4)

        # write users
        users_file = os.path.join(contest_data_folder, 'kg_cms_users.json')
        touch_container(users_file)
        users = [{
            "first_name": account.first_name,
            "last_name": account.last_name,
            "display_name": account.display_name,
            "username": account.username,
            "type": account.type,
            "password": account.password,
        } for account in accounts]
        if contest.display_timezone:
            for user in users:
                user['timezone'] = contest.display_timezone
        info_print('writing users file...', users_file)
        with open(users_file, 'w') as fl:
            json.dump(users, fl, indent=4)


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
        if args.format == 'pc2' and not contest.site_password: raise CommandError(f"site_password required for {args.format}")
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

            if args.format == 'dom':
                time_limit = details.time_limit
            else:
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


            kg_compile(format_, details, args.format, loc=problem_loc, python3=contest.python3_command)

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
                

            # write config files
            # TODO fix problem statement integration
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


            # copy statement. find one with compatible ending
            statements = [s for s in [details.statement_compiled, contest.rel_global_statements, details.statement_base] if s]
            if args.format == 'dom' and statements:
                for source in statements:
                    base, ext = os.path.splitext(source)
                    if ext in {'.pdf', '.html', '.txt'}: break
                else:
                    source = statements[0] # just take the first one
                base, ext = os.path.splitext(source)
                target = os.path.join(problems_folder, problem_code, 'problem_statement', 'statement' + ext)
                copy_file(source, target)
                target = os.path.join(problems_folder, problem_code, 'problem' + ext)
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
                dest = os.path.join(contest_folder, 'UPLOADS', 'UPLOAD_2ND_problems', letter)
                
                info_print('Zipping the whole thing...')
                info_print('target is', dest + '.zip')
                make_archive(dest, 'zip', os.path.join(problems_folder, problem_code))
                info_print('Done.')


    if not args.no_seating and contest.seating:
        decor_print()
        decor_print('-'*42)
        beginfo_print('Writing seating arrangement')
        write_seating(contest, seedval=seedval, dest=contest_folder)

    if args.format == 'dom':
        warn_print("Note: There seems to be no way to import contest configuration to DOMjudge, ")
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
                yield ts, team, idx

    def get_accounts():
        for idx, (school, team_name, school_idx) in enumerate(get_team_schools(), 1):
            account_name = args.account_format.format(
                    idx=idx,
                    school_idx=school_idx,
                    school_name=school['school'],
                    team_name=team_name,
                    first1=team_name.split()[0][0],
                    first=team_name.split()[0],
                    last1=team_name.split()[-1][0],
                    last=team_name.split()[-1],
                )
            yield Account(
                username=account_name,
                display_name=team_name,
                password=passwords[team_name],
                type='team',
                index=idx,
                type_index=idx,
                school=school['school'],
                school_short=school.get('school_short'),
                country_code=school.get('country_code'),
            )

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
