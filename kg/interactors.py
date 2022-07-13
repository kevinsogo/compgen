import argparse
import contextlib
import functools
import io
import json
import subprocess
import sys
import traceback

from .utils import * ### @import

CURR_PLATFORM = 'local' ### @replace 'local', format or 'local'

# Like BufferedRWPair, but:
# - takes in two text I/Os rather than raw I/Os
# - makes seekable() false
#
# I tried to use TextIOWrapper(BufferedRWPair(...)), but I couldn't get it to work in some instances,
# particularly when both arguments are stdin and stdout, and stdin is piped from a file. (It seems the
# decoder.reset() call drops some data.) If you can get this working, feel free to replace this with that.
#
# After some more investigation, this looks like an unfixed Python bug:
# https://github.com/python/cpython/issues/56424
# unfixed because "nobody complained about it for the last 9 years" :(
#
# Relevant "decoder.reset()" call:
# https://github.com/python/cpython/blob/ca308c13daa722f3669a14f1613da768086beb6a/Modules/_io/textio.c#L1695
# https://github.com/python/cpython/blob/cceac5dd06fdbaba3f45b8be159dfa79b74ff237/Lib/_pyio.py#L2214
class TextIOPair(io.TextIOBase):
    def __init__(self, reader, writer):
        if not reader.readable():
            raise OSError('"reader" argument must be readable')
        if not writer.writable():
            raise OSError('"writer" argument must be writable')
        self.reader = reader
        self.writer = writer
        super().__init__()

    def read(self, *args):
        return self.reader.read(*args)

    def readline(self, *args):
        return self.reader.readline(*args)

    def write(self, *args):
        return self.writer.write(*args)

    def peek(self, *args):
        return self.reader.peek(*args)

    def readable(self, *args):
        return self.reader.readable(*args)

    def writable(self, *args):
        return self.writer.writable(*args)

    def flush(self, *args):
        return self.writer.flush(*args)

    def close(self):
        try:
            self.writer.close()
        finally:
            self.reader.close()

    def isatty(self):
        return self.reader.isatty() or self.writer.isatty()

    @property
    def closed(self):
        return self.writer.closed

    @property
    def encoding(self):
        return self.writer.encoding

    @property
    def errors(self):
        return self.writer.errors

    @property
    def newlines(self):
        return self.writer.newlines

    def print(self, *args, **kwargs):
        kwargs.setdefault('file', self.writer)
        kwargs.setdefault('flush', True)
        return print(*args, **kwargs)

    def input(self):
        return self.readline().removesuffix('\n')
    
    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line



# TODO some kind of unification with checkers
class InteractorError(Exception): ...
class ParseError(InteractorError): ...
class Wrong(InteractorError): ...
class Fail(InteractorError): ...

WA = Wrong # TODO add deprecation notice when WA() is called

class Verdict:
    AC = "Success"
    PAE = "Wrong answer (Parse error)" # wrong answer due to invalid/unreadable format.
    CE = "Compile Error" # the solution didn't compile
    WA = "Wrong answer" # correct output format, incorrect answer.
    RTE = "Runtime Error" # solution crashed.
    TLE = "Time Limit Exceeded" # solution didn't finish under the specified time limit.
    EXC = "Interactor raised an error" # unintended errors of the interactor.
    FAIL = "Interactor failed" # deliberate failures, e.g. if the test data is detected as incorrect.






_polygon_rcode = {
    Verdict.AC: 0,
    Verdict.CE: 1,
    Verdict.PAE: 2,
    Verdict.WA: 1,
    Verdict.RTE: 1,
    Verdict.TLE: 1,
    Verdict.FAIL: 3,
    Verdict.EXC: 3,
}
_polygon_partial = 16

_kg_rcode = {
    Verdict.AC: 0,
    Verdict.CE: 10,
    Verdict.WA: 20,
    Verdict.RTE: 21,
    Verdict.TLE: 22,
    Verdict.PAE: 23,
    Verdict.FAIL: 30,
    Verdict.EXC: 31,
}


def write_json_verdict(verdict, message, score, result_file):
    with open(result_file, 'w') as f:
        json.dump({
            'verdict': verdict,
            'message': message,
            'score': score,
        }, f)

_xml_outcome = {
    Verdict.AC: "Accepted",
    Verdict.CE: "No - Compilation Error",
    Verdict.PAE: "No - Wrong Answer",
    Verdict.WA: "No - Wrong Answer",
    Verdict.RTE: "No - Run-time Error",
    Verdict.TLE: "No - Time Limit Exceeded",
    Verdict.FAIL: "No - Other - Contact Staff",
    Verdict.EXC: "No - Other - Contact Staff",
}
def write_xml_verdict(verdict, message, score, result_file):
    from xml.etree.ElementTree import Element, ElementTree
    result = Element('result')
    result.set('security', result_file)
    result.set('outcome', _xml_outcome[verdict])
    result.text = str(verdict) + ": " + message
    ElementTree(result).write(result_file, xml_declaration=True, encoding="utf-8")



def _interact_generic(interactor, input, *users, output=None, judge=None, **kwargs):
    # assumes files are opened, unlike its checker counterpart
    # TODO make consistent with checker counterpart

    def handle_exc_verdict(exc, verdict):
        if kwargs.get('verbose'): traceback.print_exc(limit=None) ### @replace None, -1
        return verdict, getattr(exc, 'score', 0.0), str(exc)

    files = []
    for name, file, modes in [('input', input, 'r'), ('output', output, 'w'), ('judge', judge, 'r')]:
        to_open = isinstance(file, str)
        kwargs[f'{name}_path'], file = (file, open(file, modes)) if to_open else (file or (None, None))
        files.append((file, to_open))

    with contextlib.ExitStack() as stack:
        input_file, output_file, judge_file = [
                stack.enter_context(file) if to_open else file
                for file, to_open in files]
        try:
            score = interactor(input_file, *users, output_file=output_file, judge_file=judge_file, **kwargs)
            if not (0.0 <= score <= 1.0):
                raise InteractorError(f"The interactor returned an invalid score: {score!r}")
            return Verdict.AC, score, ""
        except ParseError as exc:
            return handle_exc_verdict(exc, Verdict.PAE)
        except Wrong as exc:
            return handle_exc_verdict(exc, Verdict.WA)
        except Fail as exc:
            return handle_exc_verdict(exc, Verdict.FAIL)
        except Exception as exc:
            return handle_exc_verdict(exc, Verdict.EXC)





_platform_interactors = {}
def _register_platform_interactor(name):
    def reg(f):
        assert name not in _platform_interactors, f"{name} registered twice!"
        _platform_interactors[name] = f
        return f
    return reg


### @@if format in ('cms', 'cms-it') {
# TODO check if this works
@_register_platform_interactor('cms')
@_register_platform_interactor('cms-it')
def _interact_cms(interact, *, score_file=sys.stdout, message_file=sys.stderr, title='', help=None, **kwargs):
    desc = help or CURR_PLATFORM + (' interactor for the problem' + (f' "{title}"' if title else ''))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('user_paths', nargs='*', help='paths to the pairs of files/FIFOs from and to each user')
    args = parser.parse_args()

    from_users, to_users = args.user_paths[::2], args.user_paths[1::2]
    if len(from_users) != len(to_users):
        raise InteractorError("Invalid number of arguments: must be even")

    with contextlib.ExitStack() as stack:
        users = [
                stack.enter_context(TextIOPair(open(from_user), open(to_user, 'w')))
                for from_user, to_user in zip(from_users, to_users)
            ]
        verdict, score, message = _interact_generic(check,
                interact,
                (sys.stdin.name, sys.stdin),
                *users,
                verbose=False,
            )

    # TODO deliberate failure here if verdict is EXC, FAIL, or something

    if not message:
        if score >= 1.0:
            message = 'translate:success'
        elif score > 0:
            message = 'translate:partial'
        else:
            message = 'translate:wrong'

    print(score, file=score_file)
    print(message, file=message_file)

### @@}

### @@}


### @@ if format in ('local', 'kg', 'pg') {
@_register_platform_interactor('local')
@_register_platform_interactor('pg')
def _interact_local(interact, *, log_file=sys.stderr, force_verbose=False, exit_after=True, **kwargs):
    desc = help or (CURR_PLATFORM + (' interactor for the problem' + (f' "{title}"' if title else '')))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='input file path')
    parser.add_argument('output_path', help='output file path to write to')
    parser.add_argument('judge_path', nargs='?', help='judge file path')
    parser.add_argument('result_file', nargs='?', help='target file to contain the verdict in XML format')
    parser.add_argument('extra_args', nargs='*', help='extra arguments that will be ignored')
    parser.add_argument('-C', '--code', default='n/a', help='path to the solution used')
    parser.add_argument('-t', '--tc-id', default=None, type=int, help='test case ID, zero indexed')
    parser.add_argument('-v', '--verbose', action='store_true', help='print more details')
    parser.add_argument('--from-user', nargs='+', help='the input files/FIFOs. If absent, stdin is used.')
    parser.add_argument('--to-user', nargs='+', help='the output files/FIFOs. If absent, stdout is used.')
    args = parser.parse_args()

    verbose = force_verbose or args.verbose
    tc_id = args.tc_id or ''

    if verbose:
        if args.extra_args: print(f"{tc_id:>3} [I] Received extra args {args.extra_args}... ignoring them.", file=log_file)
        print(f"{tc_id:>3} [I] Interacting with the solution...", file=log_file)

    with contextlib.ExitStack() as stack:
        if args.from_user or args.to_user:
            if not (args.from_user and args.to_user and len(args.from_user) == len(args.to_user)):
                raise InteractorError("There must be the same number of input and output files/FIFOs.")
            users = [
                    stack.enter_context(TextIOPair(open(from_user), open(to_user, 'w')))
                    for from_user, to_user in zip(from_users, to_users)
                ]
        else:
            users = [TextIOPair(sys.stdin, sys.stdout)]

        verdict, score, message = _interact_generic(
                interact,
                args.input_path,
                *users,
                code_path=args.code,
                output=args.output_path,
                judge=args.judge_path,
                tc_id=args.tc_id,
                verbose=verbose,
            )

    if verbose:
        print(f"{tc_id:>3} [I] Result:  {verdict}", file=log_file)
        print(f"{tc_id:>3} [I] Score:   {score}", file=log_file)
        if message: print(f"{tc_id:>3} [I] Message: {overflow_ell(message, 100)}", file=log_file)
    else:
        print(f"{tc_id:>3} [I] Score={score} {verdict}", file=log_file)

    if args.result_file:
        if verbose: print(f"{tc_id:>3} [I] Writing result to '{args.result_file}'...", file=log_file)
        ### @@replace '_json_', '_json_' if format in ('local', 'kg') else '_xml_' {
        write_json_verdict(verdict, message, score, args.result_file)
        ### @@}

    if CURR_PLATFORM == 'pg':
        # assumes max score is 100. TODO learn what polygon really does
        exit_code = _polygon_partial + int(score * 100) if 0 < score < 1 else _polygon_rcode[verdict]
    else:
        exit_code = _kg_rcode[verdict]

    if exit_after:
        exit(exit_code)

    return exit_code
### @@ }

# TODO this should be a class, like checkers?
def interactor(f=None):
    def _interactor(interact):
        @functools.wraps(interact)
        def _interact(*args, platform=CURR_PLATFORM, **kwargs):
            return _platform_interactors[platform](interact, *args, **kwargs)
        return _interact
    return _interactor(f) if f is not None else _interact



# kg
# - argv[1] = input_file
# - argv[2] = output_file
# - Pair(stdin, stdout) = user
# - argv[3] = answer_file
# - argv[4] = result_file

# testlib
# - argv[1] = input_file
# - argv[2] = output_file
# - Pair(stdin, stdout) = user
# - argv[3] = answer_file
# - argv[4] = result_file
# - argv[5] = appes mode (whatever that is) [NOT SUPPORTED]
# - returncode = result

# CMS
# - stdin = input_file
# - stdout = result
# - ERROR = output_file
# - Pair(argv[1], argv[2]) = user
