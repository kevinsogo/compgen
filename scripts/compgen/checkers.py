#!/usr/bin/python2

'''
Useful stuff for custom checkers/judges.
'''

from __future__ import print_function, division, unicode_literals, absolute_import

__author__ = "Kevin Atienza"
__license__ = "MIT"
__maintainer__ = "Kevin Atienza"
__email__ = "kevin.charles.atienza@gmail.com"
__status__ = "Development"
__version__ = "0.1"

from sys import stdout, stderr
import itertools, functools, argparse


def ensure(condition, message=None, exc=Exception):
    ''' assert that doesn't raise AssertionError. Useful/Convenient for judging. '''
    if not condition:
        try:
            message = message()
        except TypeError:
            pass
        raise exc(message)


def _merge_dicts(d, *others):
    d = d.copy()
    for o in others:
        for k, v in o.items():
            if k in d: raise Exception("duplicate key: {}".format(k))
            d[k] = v
    return d


class ParseError(Exception): pass
class WA(Exception): pass
class Fail(Exception): pass


class Verdict:
    AC = "Success"
    PAE = "Wrong answer (Parse error)" # wrong answer due to invalid/unreadable format.
    WA = "Wrong answer" # correct output format, incorrect answer.
    EXC = "Checker raised an error" # unintended errors of the checker.
    FAIL = "Checker failed" # deliberate failures, e.g. if the test data is detected as incorrect.


class ChkStream(object):
    def __init__(self, stream, type_):
        self.type = type_
        self.base_stream = stream # file-like object
        if type_ == 'lines':
            def naive_iter():
                for line in stream.readlines():
                    yield line.rstrip('\n')
        elif type_ == 'tokens':
            def naive_iter():
                for line in stream.readlines():
                    for tok in line.strip().split():
                        yield tok
        else:
            raise Exception("Invalid Stream type: {}".format(type_))

        self._seq = naive_iter()

        super(ChkStream, self).__init__()

    def next(self):
        return self._seq.next()

    def has_next(self):
        try:
            self.peek()
            return True
        except StopIteration:
            return False

    def peek(self):
        v = self._seq.next()
        self._seq = itertools.chain([v], self._seq)
        return v

    def __iter__(self):
        return self


# an enum of accepted _Set names
class _SN:
    get_one_input = 'get_one_input'
    get_output_from_input = 'get_output_from_input'
    get_judge_data_from_input = 'get_judge_data_from_input'
    problem_title = 'problem_title'
    aggregate = 'aggregate'
    iterator = 'iterator'


class Checker(object):
    def __init__(self):
        self._vals = {}
        for name in [_SN.get_one_input,
                     _SN.get_output_from_input,
                     _SN.get_judge_data_from_input,
                     _SN.problem_title,
                     _SN.aggregate,
                     _SN.iterator,
                ]:
            setattr(self, name, functools.partial(self._set, name))
        super(Checker, self).__init__()

    def _set(self, name, value):
        self._vals[name] = value
        return value

    def __call__(self, *args, **kwargs):
        return self.run('local', *args, **kwargs)

    def run(self, platform, *args, **kwargs):
        _actual = _platforms.get(platform)
        if _actual: return _actual(self.checker, *args, **kwargs)

    def set_checker(self, *args, **kwargs):
        sdata = args
        if not sdata: sdata = 'lines',
        if len(sdata) == 1: sdata = sdata*3
        if len(sdata) != 3: raise Exception("Invalid args: {}".format(args))
        intype, outtype, judgetype = sdata
        no_extra_chars = kwargs.pop('no_extra_chars', False)
        def _set_checker(checker):
            def _checker(inp, outp, judgep, *args, **kwargs):
                inp = ChkStream(inp, intype)
                outp = ChkStream(outp, outtype)
                judgep = ChkStream(judgep, judgetype)
                result = checker(inp, outp, judgep, *args, **kwargs)
                if no_extra_chars:
                    if inp.has_next(): raise Fail("Extra characters at the end of the input file!")
                    if outp.has_next(): raise WA("Extra characters at the end of the output file.")
                    if judgep.has_next(): raise Fail("Extra characters at the end of the judge file!")
                return result
            self.checker = _checker
            return checker
        return _set_checker

    def set_single_checker(self, *args, **kwargs):
        def _set_single_checker(check_test_case):
            self.set_checker(*args, **kwargs)(functools.partial(self._check_single, check_test_case))
            return check_test_case
        return _set_single_checker

    def set_multi_checker(self, *args, **kwargs):
        def _set_multi_checker(check_test_case):
            self.set_checker(*args, **kwargs)(functools.partial(self._check_multi, check_test_case))
            return check_test_case
        return _set_multi_checker

    def _check_single(self, check_test_case, input_file, output_file, judge_file, **kwargs):
        get_one_input = self._vals[_SN.get_one_input]
        get_output_from_input = self._vals[_SN.get_output_from_input]
        get_judge_data_from_input = self._vals[_SN.get_judge_data_from_input]

        inp = get_one_input(input_file, **_merge_dicts({'exc': Fail}, kwargs))
        outp = get_output_from_input(output_file, inp, **_merge_dicts({'exc': ParseError}, kwargs))
        judgep = get_judge_data_from_input(judge_file, inp, **_merge_dicts({'exc': Fail}, kwargs))
        return check_test_case(inp, outp, judgep, **kwargs)

    def _check_multi(self, check_test_case, input_f, output_f, judge_f, **kwargs):
        get_one_input = self._vals[_SN.get_one_input]
        get_output_from_input = self._vals[_SN.get_output_from_input]
        get_judge_data_from_input = self._vals[_SN.get_judge_data_from_input]
        aggregate = self._vals.get(_SN.aggregate, minimum_score)
        iterator = self._vals.get(_SN.iterator, iterate_with_casecount)

        class It(object):
            @staticmethod
            def get_score(inp, outp, judgep, **kw):
                return check_test_case(inp, outp, judgep, **_merge_dicts(kw, kwargs))

            @staticmethod
            def next_input(**kw):
                return get_one_input(input_f, **_merge_dicts(kw, {'exc': Fail}, kwargs))

            @staticmethod
            def next_output(inp, **kw):
                return get_output_from_input(output_f, inp, **_merge_dicts(kw, {'exc': ParseError}, kwargs))

            @staticmethod
            def next_judge_data(inp, **kw):
                return get_judge_data_from_input(judge_f, inp, **_merge_dicts(kw, {'exc': Fail}, kwargs))

            input_file = input_f
            output_file = output_f
            judge_file = judge_f

        return aggregate(iterator(It))


def _check_generic(checker, input_path, output_path, judge_path, **kwargs):
    with open(input_path) as input_file:
        with open(output_path) as output_file:
            with open(judge_path) as judge_file:
                try:
                    score = checker(input_file, output_file, judge_file, **kwargs)
                    return Verdict.AC, score, ""
                except ParseError as exc:
                    verdict = Verdict.PAE
                except WA as exc:
                    verdict = Verdict.WA
                except Fail as exc:
                    verdict = Verdict.FAIL
                except Exception as exc:
                    verdict = Verdict.EXC
                return verdict, getattr(exc, 'score', 0.0), str(exc)


_platforms = {}
def _register_platform(name):
    def reg(f):
        assert name not in _platforms, "{} registered twice!".format(name)
        _platforms[name] = f
        return f
    return reg


_hr_verdict_name = {
    Verdict.AC: "Success",
    Verdict.PAE: "Wrong Answer",
    Verdict.WA: "Wrong Answer",
    Verdict.FAIL: "Checker Failed",
    Verdict.EXC: "Checker Failed.", # Added a dot so we can recognize which kind of failure it is.
}
@_register_platform('hr')
def _check_hr(checker, t_obj, r_obj, print_message=False):
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
        r_obj.result = verdict == Verdict.ac
        r_obj.message = _hr_verdict_name[verdict]

    if print_message and message:
        print(message, file=stderr)


_polygon_rcode = {
    Verdict.AC: 0,
    Verdict.PAE: 2,
    Verdict.WA: 1,
    Verdict.FAIL: 3,
    Verdict.EXC: 3,
}
@_register_platform('local') # @@@ remove to suppress
@_register_platform('polygon') # AFAIK, they are currently identical in behavior
def _check_local(checker, title='', file=stdout):
    desc = 'Judge for the problem "{}"'.format(title) if title else 'Judge for the problem'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='Input file path')
    parser.add_argument('output_path', help="Contestant's file path")
    parser.add_argument('judge_path', help='Judge auxiliary data file path')
    parser.add_argument('-c', '--code', default='n/a', help='Path to the solution used')
    parser.add_argument('-t', '--tc-id', default=None, type=int, help='Test case ID, zero indexed')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print more details')
    parser.add_argument('-i', '--identical', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    tc_id = args.tc_id if args.tc_id is not None else ''

    if args.verbose: print("{:>2} Checking the output...".format(tc_id), file=file)
    verdict, score, message = _check_generic(checker,
            input_path=args.input_path,
            output_path=args.output_path,
            judge_path=args.judge_path,
            code_path=args.code,
            tc_id=args.tc_id,
            identical=args.identical,
        )

    if args.verbose:
        print("{:>2} Result:  {}".format(tc_id, verdict), file=file)
        print("{:>2} on HR:   {}".format(tc_id, _hr_verdict_name[verdict]), file=file)
        print("{:>2} Score:   {}".format(tc_id, score), file=file)
        if message: print("{:>2} Message: {}".format(tc_id, message), file=file)
    else:
        print("{:>2} Score={} {}".format(tc_id, score, verdict), file=file)

    exit(_polygon_rcode[verdict])


def minimum_score(scores, mn=0.0, mx=1.0, exc=Fail):
    m = mx
    for score in scores:
        if score is None:
            raise exc("The checker returned a score of 'None'.")
        if not (mn <= score <= mx):
            raise exc("Invalid score: {}. It must be in the interval [{}, {}].".format(score, mn, mx))
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
    z = int(it.input_file.next())
    for cas in xrange(z):
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

def abs_rel_error(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1)

chk = Checker() # create singleton

set_checker = chk.set_checker
set_single_checker = chk.set_single_checker
set_multi_checker = chk.set_multi_checker
