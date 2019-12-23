from enum import Enum
from sys import stdout, stderr
import os.path
import itertools, functools, argparse, traceback

from .utils import * ### @import

CURR_PLATFORM = 'local' ### @replace 'local', format

def _merge_dicts(d, *others):
    d = d.copy()
    for o in others:
        for k, v in o.items():
            if k in d: raise ValueError(f"duplicate key: {k}")
            d[k] = v
    return d


class CheckerError(Exception): ...
class ParseError(CheckerError): ...
class WA(CheckerError): ...
class Fail(CheckerError): ...


class Verdict:
    AC = "Success"
    PAE = "Wrong answer (Parse error)" # wrong answer due to invalid/unreadable format.
    CE = "Compile Error" # the solution didn't compile
    WA = "Wrong answer" # correct output format, incorrect answer.
    RTE = "Runtime Error" # solution crashed.
    TLE = "Time Limit Exceeded" # solution didn't finish under the specified time limit.
    EXC = "Checker raised an error" # unintended errors of the checker.
    FAIL = "Checker failed" # deliberate failures, e.g. if the test data is detected as incorrect.


class ChkStream:
    def __init__(self, stream, type_, exc=Fail):
        self.type = type_
        self.base_stream = stream # file-like object
        if type_ == 'lines':
            def naive_iter():
                try:
                    for line in stream.readlines():
                        yield line.rstrip('\n')
                except Exception as e:
                    raise exc from e
        elif type_ == 'tokens':
            def naive_iter():
                try:
                    for line in stream.readlines():
                        yield from line.strip().split()
                except Exception as e:
                    raise exc from e
        elif type_ == 'raw_lines':
            def naive_iter():
                try:
                    for line in stream.readlines():
                        yield line
                except Exception as e:
                    raise exc from e
        else:
            raise ValueError(f"Invalid Stream type: {type_}")

        self._seq = naive_iter()

        super().__init__()

    def __next__(self):
        return next(self._seq)

    def has_next(self):
        try:
            self.peek()
            return True
        except StopIteration:
            return False

    def peek(self):
        v = next(self._seq)
        self._seq = itertools.chain([v], self._seq)
        return v

    def __iter__(self):
        return self


# an enum of accepted _Set names
_SetName = Enum('_SetName', ['get_one_input', 'get_output_for_input', 'get_judge_data_for_input', 'problem_title', 'aggregate', 'iterator'])

class Checker:
    def __init__(self):
        self._vals = {}
        for sn in _SetName: setattr(self, sn.name, functools.partial(self._set, sn))

        # aliases for backwards compatibility. I imagine these will be removed after some time.
        def warn_on_use(wrong, correct, f):
            ''' print a warning when the alias is used instead of the correct one. '''
            @functools.wraps(f)
            def warn_f(*args, **kwargs):
                print(f'Deprecation warning: Please use {correct} instead of {wrong}', file=stderr) ### @if False
                return f(*args, **kwargs)
            # just return 'f' if we're not printing the warning anyway ### @if False
            return warn_f ### @replace 'warn_f', 'f'
        for wrong_name, correct_name in [
                ('get_output_from_input', 'get_output_for_input'),
                ('get_judge_data_from_input', 'get_judge_data_for_input'),
            ]:
            setattr(self, wrong_name, warn_on_use(wrong_name, correct_name, getattr(self, correct_name)))

        super().__init__()

    def _set(self, sn, value):
        self._vals[sn] = value
        return value

    def __call__(self, *args, **kwargs):
        ...
        return self.run(CURR_PLATFORM, *args, **kwargs) ### @if format != 'hr'

    def run(self, platform, *args, **kwargs):
        _actual = _platforms.get(platform)
        if _actual: return _actual(self.checker, *args, **kwargs)

    def set_checker(self, *args, **kwargs):
        sdata = args
        if not sdata: sdata = 'lines',
        if len(sdata) == 1: sdata = sdata*3
        if len(sdata) != 3: raise ValueError(f"Invalid args: {args}")
        intype, outtype, judgetype = sdata
        no_extra = kwargs.pop('no_extra_chars', False)
        valid_fields = ['input', 'output', 'judge']
        if isinstance(no_extra, bool):
            no_extra = valid_fields if no_extra else []
        if not set(no_extra) <= set(valid_fields): raise ValueError(f"Invalid no_extra_chars argument: {no_extra!r}")
        extra_msg = lambda file: f"Extra characters at the end of the {file}"
        def _set_checker(checker):
            def _checker(inp, outp, judgep, *args, **kwargs):
                inp = ChkStream(inp, intype)
                outp = ChkStream(outp, outtype, exc=WA)
                judgep = ChkStream(judgep, judgetype)
                result = checker(inp, outp, judgep, *args, **kwargs)
                if no_extra:
                    if 'input' in no_extra and inp.has_next(): raise Fail(extra_msg("input file!"))
                    if 'output' in no_extra and outp.has_next(): raise WA(extra_msg("output file."))
                    if 'judge' in no_extra and judgep.has_next(): raise Fail(extra_msg("judge file!"))
                return result
            self.checker = _checker
            return checker
        return _set_checker

    def set_single_checker(self, *args, **kwargs):
        def _set_single_checker(check_test_case):
            self.set_checker(*args, **kwargs)(functools.partial(self._check_multi, check_test_case, _iterator=iterate_single))
            return check_test_case
        return _set_single_checker

    def set_multi_checker(self, *args, **kwargs):
        def _set_multi_checker(check_test_case):
            self.set_checker(*args, **kwargs)(functools.partial(self._check_multi, check_test_case))
            return check_test_case
        return _set_multi_checker

    def _check_multi(self, check_test_case, input_f, output_f, judge_f, *, _aggregate=None, _iterator=None, **kwargs):
        get_one_input = self._vals[_SetName.get_one_input]
        get_output_for_input = self._vals[_SetName.get_output_for_input]
        get_judge_data_for_input = self._vals[_SetName.get_judge_data_for_input]

        def catch_spec_as(exc):
            def _catch(f):
                @functools.wraps(f)
                def _wrapped(*a, **kw):
                    try:
                        return f(*a, **kw)
                    except StopIteration as st:
                        raise exc from st
                return _wrapped
            return _catch

        aggregate = _aggregate or self._vals.get(_SetName.aggregate, minimum_score)
        iterator = _iterator or self._vals.get(_SetName.iterator, iterate_with_casecount)

        aggregate = catch_spec_as(Fail("aggregate function failed"))(aggregate)
        iterator = catch_spec_as(Fail("iterator function failed"))(iterator)

        class It:
            @staticmethod
            @catch_spec_as(Fail("check_test_case failed"))
            def get_score(inp, outp, judgep, **kw):
                return check_test_case(inp, outp, judgep, **kw, **kwargs)

            @staticmethod
            @catch_spec_as(Fail("Input file fully read but expected more"))
            def next_input(**kw):
                return get_one_input(input_f, **kw, exc=Fail, **kwargs)

            @staticmethod
            @catch_spec_as(ParseError("Output file fully read but expected more"))
            def next_output(inp, **kw):
                return get_output_for_input(output_f, inp, **kw, exc=ParseError, **kwargs)

            @staticmethod
            @catch_spec_as(Fail("Judge file fully read but expected more"))
            def next_judge_data(inp, **kw):
                return get_judge_data_for_input(judge_f, inp, **kw, exc=Fail, **kwargs)

            input_file = input_f
            output_file = output_f
            judge_file = judge_f

        return aggregate(iterator(It))


def _check_generic(checker, input_path, output_path, judge_path, **kwargs):
    ### @@if format == 'pc2' {
    if CURR_PLATFORM == 'pc2' and os.path.isfile('EXITCODE.TXT'): # WTH undocumented shit PC^2 !?!?
        return Verdict.RTE, 0.0, "The solution didn't return a 0 exit code (maybe... because EXITCODE.TXT exists)."
    ### @@}

    kwargs.update({'input_path': input_path, 'output_path': output_path, 'judge_path': judge_path})

    if CURR_PLATFORM in {'cms', 'cms-it'}:
        def handle_exc_verdict(exc, verdict):
            return verdict, getattr(exc, 'score', 0.0), ""
    else:
        def handle_exc_verdict(exc, verdict):
            if kwargs.get('verbose'): traceback.print_exc()
            return verdict, getattr(exc, 'score', 0.0), str(exc)

    try:
        input_file, output_file, judge_file = map(open, (input_path, output_path, judge_path))
    except Exception as exc:
        return handle_exc_verdict(exc, Verdict.EXC)
    with input_file, output_file, judge_file:
        try:
            score = checker(input_file, output_file, judge_file, **kwargs)
            if not (0.0 <= score <= 1.0): return Verdict.FAIL, 0.0, f"The checker returned an invalid score: {score!r}"
            return Verdict.AC, score, ""
        except ParseError as exc:
            return handle_exc_verdict(exc, Verdict.PAE)
        except WA as exc:
            return handle_exc_verdict(exc, Verdict.WA)
        except Fail as exc:
            return handle_exc_verdict(exc, Verdict.FAIL)
        except Exception as exc:
            return handle_exc_verdict(exc, Verdict.EXC)


_platforms = {}
def _register_platform(name):
    def reg(f):
        assert name not in _platforms, f"{name} registered twice!"
        _platforms[name] = f
        return f
    return reg


_hr_verdict_name = {
    Verdict.AC: "Success",
    Verdict.CE: "Compilation Error",
    Verdict.PAE: "Wrong Answer",
    Verdict.WA: "Wrong Answer",
    Verdict.RTE: "Runtime Error",
    Verdict.TLE: "Time limit exceeded", # I don't like HR's message "terminated due to timeout"
    Verdict.FAIL: "Checker Failed",
    Verdict.EXC: "Checker Failed.", # Added a dot so we can recognize which kind of failure it is.
}

### @@if format == 'hr' {
@_register_platform('hr')
def _check_hr(checker, t_obj, r_obj, *, print_message=False):
    if t_obj.testcase_signal:
        message = ""
        r_obj.result = False
        r_obj.score = 0.0
        r_obj.message = "Runtime Error"
    else:
        verdict, r_obj.score, message = _check_generic(checker,
                input_path=t_obj.testcase_input_path,
                output_path=t_obj.testcase_output_path,
                judge_path=t_obj.testcase_expected_output_path,
                code_path=t_obj.submission_code_path,
                tc_id=t_obj.testcase_id,
                identical=t_obj.testcase_result,
            )
        r_obj.result = verdict == Verdict.AC
        r_obj.message = _hr_verdict_name[verdict]

    if print_message and message: print(message, file=stderr)
### @@ }

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

### @@if format in ('local', 'kg') {
def write_json_verdict(verdict, message, score, result_file):
    with open(result_file, 'w') as f:
        json.dump({
            'verdict': verdict,
            'message': message,
            'score': score,
        }, f)
### @@}

### @@if format in ('pg', 'pc2') {
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
### @@}

### @@if format in ('cms', 'cms-it') {
# CMS has a specific format in stdout and stderr, so we make it stricter
@_register_platform('cms')
@_register_platform('cms-it')
def _check_cms(checker, *, score_file=stdout, message_file=stderr, title='', help=None, **kwargs):
    desc = help or CURR_PLATFORM + (' judge for the problem' + (f' "{title}"' if title else ''))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='input file path')
    parser.add_argument('judge_path', help='judge auxiliary data file path')
    parser.add_argument('output_path', help="contestant's file path")
    parser.add_argument('extra_args', nargs='*', help='extra arguments that will be ignored')
    args = parser.parse_args()

    verdict, score, message = _check_generic(checker,
            input_path=args.input_path,
            output_path=args.output_path,
            judge_path=args.judge_path,
        )

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

### @@if format in ('local', 'kg', 'pg', 'pc2') {
@_register_platform('local')
@_register_platform('kg')
@_register_platform('pg')
@_register_platform('pc2')
def _check_local(checker, title='', file=stdout, help=None, force_verbose=False):
    desc = help or CURR_PLATFORM + (' judge for the problem' + (f' "{title}"' if title else ''))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='input file path')
    parser.add_argument('output_path', help="contestant's file path")
    parser.add_argument('judge_path', help='judge auxiliary data file path')
    parser.add_argument('result_file', nargs='?', help='target file to contain the verdict in XML format')
    parser.add_argument('extra_args', nargs='*', help='extra arguments that will be ignored')
    parser.add_argument('-c', '--code', default='n/a', help='path to the solution used')
    parser.add_argument('-t', '--tc-id', default=None, type=int, help='test case ID, zero indexed')
    if CURR_PLATFORM == 'pc2':
        parser.add_argument('-q', '--quiet', action='store_true', help='print less details')
    else:
        parser.add_argument('-v', '--verbose', action='store_true', help='print more details')
    parser.add_argument('-i', '--identical', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    verbose = force_verbose or (not args.quiet if CURR_PLATFORM == 'pc2' else args.verbose)
    tc_id = args.tc_id or ''

    if verbose:
        if args.extra_args: print(f"{tc_id:>2} Received extra args {args.extra_args}... ignoring them.", file=file)
        print(f"{tc_id:>2} Checking the output...", file=file)

    verdict, score, message = _check_generic(checker,
            input_path=args.input_path,
            output_path=args.output_path,
            judge_path=args.judge_path,
            code_path=args.code,
            tc_id=args.tc_id,
            identical=args.identical,
            verbose=verbose,
        )

    if verbose:
        print(f"{tc_id:>2} Result:  {verdict}", file=file)
        print(f"{tc_id:>2} on HR:   {_hr_verdict_name[verdict]}", file=file)
        print(f"{tc_id:>2} Score:   {score}", file=file)
        if message: print(f"{tc_id:>2} Message: {overflow_ell(message, 100)}", file=file)
    else:
        print(f"{tc_id:>2} Score={score} {verdict}", file=file)

    if args.result_file:
        if verbose: print(f"{tc_id:>2} Writing result to {args.result_file}...", file=file)
        ### @@replace '_json_', '_json_' if format in ('local', 'kg') else '_xml_' {
        write_json_verdict(verdict, message, score, args.result_file)
        ### @@}

    exit(_polygon_rcode[verdict])
### @@ }

def minimum_score(scores, mn=0.0, mx=1.0, exc=Fail):
    m = mx
    for score in scores:
        if score is None:
            raise exc("The checker returned a score of 'None'.")
        if not (mn <= score <= mx):
            raise exc(f"Invalid score: {score}. It must be in the interval [{mn}, {mx}].")
        m = min(m, score)
        if m == mn: break # we can stop now
    return m


def average_score(scores, exc=Fail):
    tl = ct = 0
    for score in scores:
        if score is None:
            raise exc("The checker returned a score of 'None'.")
        tl += score
        ct += 1
    return tl / ct


def iterate_with_casecount(it):
    z = int(next(it.input_file))
    for cas in range(z):
        inp = it.next_input(caseno=cas)
        yield it.get_score(inp, it.next_output(inp, caseno=cas), it.next_judge_data(inp, caseno=cas), caseno=cas)

def iterate_single(it, *, cas=0):
    inp = it.next_input(caseno=cas)
    yield it.get_score(inp, it.next_output(inp, caseno=cas), it.next_judge_data(inp, caseno=cas), caseno=cas)

def default_return(ret):
    def _default_return(f):
        @functools.wraps(f)
        def new_f(*args, **kwargs):
            res = f(*args, **kwargs)
            if res is None: res = ret
            return res
        return new_f
    return _default_return

default_score = default_return(1.0)

chk = Checker() # create singleton

set_checker = chk.set_checker
set_single_checker = chk.set_single_checker
set_multi_checker = chk.set_multi_checker

### @@if format == 'hr' {

from .utils.hr import * ### @import
### @@if subtasks_only {
###     @set write = True
### @@}

valid_subtasks = None ### @replace None, repr(sorted(details.valid_subtasks))
subtasks_files = None ### @replace None, '[\n{}]'.format(''.join(f'    (({l}, {r}), {subs!r}),\n' for l, r, subs in subtasks_files))

if valid_subtasks:
    ... ### @@ if details.valid_subtasks {

    # change this for every problem just to be safe
    tmp_filename_base = '/tmp/hr_custom_checker_monika_' ### @replace "monika", unique_name()

    # under the testcases tab, if a file is the last file for some subtask (which should be unique),
    # set the weight of the file to be the number of points for the subtask.
    # set the weight of the remaining files to be 0.  

    subtasks_of, last_file_of = hr_parse_subtasks(valid_subtasks, subtasks_files, compiled=False) ### @replace False, True

    def clear_tmp(filename):
        try:
            import os
            os.remove(filename)
        except OSError:
            pass

    def run_custom_checker(t_obj, r_obj):
        tmp_filename = tmp_filename_base + str(sum(map(ord, t_obj.submission_code_path)))

        test_id = t_obj.testcase_id
        ensure(test_id in subtasks_of, "Testcase id invalid: %s" % (test_id))
        curr_subtasks = subtasks_of[test_id]

        if test_id == 0:
            previous_scores = {}
        else:
            try:
                with open(tmp_filename) as f:
                    previous_scores = json.load(f)
                previous_scores = {int(k): v for k, v in previous_scores.items()}
            except Exception:
                previous_scores = {}


        for subtask in valid_subtasks:
            previous_scores.setdefault(subtask, 1.0)

        chk.run('hr', t_obj, r_obj, print_message=False)

        for subtask in curr_subtasks:
            previous_scores[subtask] = min(previous_scores[subtask], r_obj.score)

        r_obj.score = 0

        for subtask in curr_subtasks:
            if last_file_of[subtask] == test_id:
                r_obj.score = previous_scores[subtask]
                break

        with open(tmp_filename, 'w') as f:
            json.dump(previous_scores, f)


    ### @@ }
else:
    ... ### @@if not details.valid_subtasks {
    def run_custom_checker(t_obj, r_obj):
        chk.run('hr', t_obj, r_obj, print_message=False)

    ### @@ }


### @@if subtasks_only {
###     @set write = False
### @@}

### @@}
