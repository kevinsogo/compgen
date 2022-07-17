import argparse, collections, contextlib, enum, functools, itertools, os, os.path, sys, traceback

from .utils import * ### @import
from .utils.streams import * ### @import
from .utils.judging import * ### @import

class CheckerError(Exception): ...

class Checker:
    def __call__(self, input_file, output_file, judge_file, *args, **kwargs):
        with contextlib.ExitStack() as stack:
            input_s = stack.enter_context(InteractiveStream(
                input_file,
                mode=ISMode(self.input_mode),
                exc=lambda message: Fail(f'[input] {message}'),
                **self.stream_settings['input'],
            ))
            output_s = stack.enter_context(InteractiveStream(
                output_file,
                mode=ISMode(self.output_mode),
                exc=ParseError,
                **self.stream_settings['output'],
            ))
            judge_s = stack.enter_context(InteractiveStream(
                judge_file,
                mode=ISMode(self.judge_mode),
                exc=lambda message: Fail(f'[judge] {message}'),
                **self.stream_settings['judge'],
            )) if judge_file else None

            return self.check(input_s, output_s, judge_s, *args, **kwargs)

    def init(self, *args, **kwargs):
        # parse options

        # TODO use kwargs for these...?
        if not args: args = ['lines']
        if len(args) == 1: args = args*3
        if len(args) != 3: raise ValueError(f"Invalid args: {args}")
        self.input_mode, self.output_mode, self.judge_mode = args

        valid_fields = {'input', 'output', 'judge'}
        def to_fields(arg):
            value = kwargs.pop(arg, False)
            value = {*value} if not isinstance(value, bool) else valid_fields if value else set()
            if not value <= valid_fields:
                raise ValueError(f"Invalid {arg} argument(s): {value - valid_fields}")
            return value

        if 'no_extra_chars' in kwargs:
            warn("'no_extra_chars' deprecated, use 'extra_chars_allowed' (Note: it's the opposite!)") ### @if False
            if 'extra_chars_allowed' in kwargs:
                raise ValueError("'no_extra_chars' and 'extra_chars_allowed' not allowed together")
            kwargs['extra_chars_allowed'] = valid_fields - to_fields('no_extra_chars')
        kwargs.setdefault('extra_chars_allowed', {'input', 'judge'})

        ### @@ if False {
        # TODO parse InteractiveStream arguments from kwargs more properly?
        # This assumes all settings are bools, and they all default to False.
        # We want to support different options for all three streams, nicely
        # and also proper handling of defaults (ISTREAM_DEFAULTS)
        ### @@ }
        fields = [(key, to_fields(key)) for key in [*kwargs]]
        self.stream_settings = {type_: {key: True for key, types in fields if type_ in types} for type_ in valid_fields}

    @classmethod
    def from_func(cls, *args, **kwargs):
        f, args = pop_callable(args)
        def _checker(f):
            check = cls()
            check.check = f
            check.init(*args, **kwargs)
            return check
        return _checker(f) if f is not None else _checker


# hmm, this is almost like just a dataclass
class BuiltChecker(Checker):
    _names = {'get_one_input', 'get_output_for_input', 'get_judge_data_for_input', 'aggregate', 'iterate', 'check_one', 'wrap_up'}
    _aliases = {
        'get_output_from_input': 'get_output_for_input',
        'get_judge_data_from_input': 'get_judge_data_for_input',
        'iterator': 'iterate',
    }
    def __init__(self):
        for name in self._names: setattr(self, name, None)
        super().__init__()

    def init(self, *args, cases=None, **kwargs):
        if cases is None:
            pass
        elif cases == 'multi':
            self._set('iterate', checker_iterate_with_casecount)
        elif cases == 'single':
            self._set('iterate', checker_iterate_single)
        else:
            raise ValueError(f"Unknown 'cases' argument: {cases}")
        super().init(*args, **kwargs)

    def _set(self, name, arg):
        if name in self._aliases:
            name, wrong_name = self._aliases[name], name
            warn_deprec_name(wrong_name, name) ### @if False
        if name not in self._names:
            raise ValueError(f"Unknown name to set: {name}")
        if getattr(self, name):
            raise ValueError(f"{name} already set!")
        setattr(self, name, arg)
        return arg

    def check(self, *args, **kwargs):
        return CheckingContext(self, *args, **kwargs)()




class CheckingContext:
    def __init__(self, checker, input_s, output_s, judge_s, **kwargs):
        self.checker = checker
        self.input_stream  = input_s
        self.output_stream = output_s
        self.judge_stream  = judge_s
        self.kwargs = kwargs
        self.input_file  = deprec_alias('input_file', self.input_stream, new_name='input_stream')
        self.output_file = deprec_alias('output_file', self.output_stream, new_name='output_stream')
        self.judge_file  = deprec_alias('judge_file', self.judge_stream, new_name='judge_stream')
        super().__init__()

    @on_exhaust(Fail("Input stream fully read but expected more"))
    def get_one_input(self, **kwargs):
        return self.checker.get_one_input(self.input_stream, exc=Fail, **kwargs, **self.kwargs)

    @on_exhaust(ParseError("Contestant output stream fully read but expected more"))
    def get_output_for_input(self, input, **kwargs):
        return self.checker.get_output_for_input(self.output_stream, input, exc=ParseError, **kwargs, **self.kwargs)

    @on_exhaust(Fail("Judge data stream fully read but expected more"))
    def get_judge_data_for_input(self, input, **kwargs):
        get_data = self.checker.get_judge_data_for_input or self.checker.get_output_for_input
        if not get_data: return
        return get_data(self.judge_stream, input, exc=Fail, **kwargs, **self.kwargs)

    @on_exhaust(Fail("aggregate function failed"))
    def aggregate(self, scores):
        return (self.checker.aggregate or minimum_score)(scores)

    @on_exhaust(Fail("iterate function failed"))
    def iterate(self):
        return (self.checker.iterate or checker_iterate_with_casecount)(self)

    @on_exhaust(Fail("check_one function failed"))
    def check_one(self, input, output, judge_data, **kwargs):
        return self.checker.check_one(input, output, judge_data, **kwargs, **self.kwargs)

    # warn on alias usage
    get_score       = deprec_alias('get_score', check_one)
    next_input      = deprec_alias('next_input', get_one_input)
    next_output     = deprec_alias('next_output', get_output_for_input)
    next_judge_data = deprec_alias('next_judge_data', get_judge_data_for_input)

    @on_exhaust(Fail("wrap_up function failed"))
    def wrap_up(self, success, score, raised_exc, **kwargs):
        if not self.checker.wrap_up: return
        return self.checker.wrap_up(success, score=score, raised_exc=raised_exc, **kwargs, **self.kwargs)

    def __call__(self):
        # will only wrap up on success or on Wrong/ParseError.
        try:
            score = self.aggregate(self.iterate())
        except (Wrong, ParseError) as exc:
            self.wrap_up(success=False, score=None, raised_exc=exc)
            raise
        else:
            new_score = self.wrap_up(success=True, score=score, raised_exc=None)
            return new_score if new_score is not None else score


def make_checker_builder():
    return Builder(name='checker', build_standalone=Checker.from_func, build_from_parts=BuiltChecker)

checker = make_checker_builder()


def checker_iterate_with_casecount(it):
    t = int(next(it.input_stream))
    for cas in range(t):
        inp = it.get_one_input(caseno=cas)
        yield it.check_one(inp,
            it.get_output_for_input(inp, caseno=cas),
            it.get_judge_data_for_input(inp, caseno=cas),
            caseno=cas,
        )


def checker_iterate_single(it, *, cas=0):
    inp = it.get_one_input(caseno=cas)
    yield it.check_one(inp,
        it.get_output_for_input(inp, caseno=cas),
        it.get_judge_data_for_input(inp, caseno=cas),
        caseno=cas,
    )





# support for old-style checkers
class OldChecker:
    def __init__(self):
        self.pending = BuiltChecker()
        self.checker = None
        for name in (*self.pending._names, *self.pending._aliases):
            setattr(self, name, functools.partial(self._set, name))
        self.init_args = None
        self.init_kwargs = None
        super().__init__()

    def _set(self, name, arg):
        if self.checker: raise RuntimeError("Cannot change checker anymore once called")
        return self.pending._set(name, arg)

    def set_single_checker(self, *args, **kwargs):
        return self.set_checker(*args, cases='single', **kwargs)

    def set_multi_checker(self, *args, **kwargs):
        return self.set_checker(*args, cases='multi', **kwargs)

    def set_checker(self, *args, **kwargs):
        f, args = pop_callable(args)
        self.init_args = args
        self.init_kwargs = kwargs
        def _set_checker(f):
            self._set('check_one', f)
            return f
        return _set_checker(f) if f is not None else _set_checker

    def __call__(self, *args, **kwargs):
        if self.checker is None:
            self.checker = self.pending
            self.checker.init(*self.init_args, **self.init_kwargs)
            self.pending = None
        return check_files(self.checker, *args, **kwargs)

# warn when any of these are used
chk = OldChecker() # create singleton
_warner = lambda name: lambda f: f
_warner = lambda name: warn_on_call(f"'{name}' deprecated. Please use new-style format via 'checker'. See the updated docs.") ### @if False
set_single_checker = _warner('set_single_checker')(chk.set_single_checker)
set_multi_checker = _warner('set_multi_checker')(chk.set_multi_checker)
@_warner('set_checker')
def set_checker(*args, **kwargs):
    chk.checker = None
    chk.pending = None
    f, args = pop_callable(args)
    def _set_checker(f):
        chk.checker = Checker.from_func(f, *args, **kwargs)
        chk.pending = None
        return chk.checker
    return _set_checker(f) if f is not None else _set_checker








def _check_generic(check, input=None, output=None, judge=None, **kwargs):
    ### @@if format == 'pc2' {
    if CURR_PLATFORM == 'pc2' and os.path.isfile('EXITCODE.TXT'): # WTH undocumented shit PC^2 !?!?
        return Verdict.RTE, 0.0, "The solution didn't return a 0 exit code (maybe... because EXITCODE.TXT exists)."
    ### @@}

    if CURR_PLATFORM in {'cms', 'cms-it'}:
        def handle_exc_verdict(exc, verdict):
            return verdict, getattr(exc, 'score', 0.0), ""
    else:
        def handle_exc_verdict(exc, verdict):
            if kwargs.get('verbose'): traceback.print_exc(limit=None) ### @replace None, -1
            return verdict, getattr(exc, 'score', 0.0), str(exc)

    with contextlib.ExitStack() as stack:

        def maybe_open(arg, mode='r'):
            if arg is None:
                return None, None
            if isinstance(arg, str):
                return arg, stack.enter_context(open(arg, mode))
            return arg

        kwargs['input_path'],  input_f  = maybe_open(input)
        kwargs['output_path'], output_f = maybe_open(output)
        kwargs['judge_path'],  judge_f  = maybe_open(judge)

        try:
            score = check(input_f, output_f, judge_f, **kwargs)
            if not (0.0 <= score <= 1.0):
                raise CheckerError(f"The checker returned an invalid score: {score!r}")
            return Verdict.AC, score, ""
        except ParseError as exc:
            return handle_exc_verdict(exc, Verdict.PAE)
        except Wrong as exc:
            return handle_exc_verdict(exc, Verdict.WA)
        except Fail as exc:
            return handle_exc_verdict(exc, Verdict.FAIL)
        except Exception as exc:
            return handle_exc_verdict(exc, Verdict.EXC)










_platform_checkers = {}
def _register_platform_checker(name):
    def reg(f):
        assert name not in _platform_checkers, f"{name} registered twice!"
        _platform_checkers[name] = f
        return f
    return reg



### @@if format == 'hr' {
@_register_platform_checker('hr')
def _check_hr(check, t_obj, r_obj, *, print_message=False):
    if t_obj.testcase_signal:
        message = ""
        r_obj.result = False
        r_obj.score = 0.0
        r_obj.message = "Runtime Error"
    else:
        verdict, r_obj.score, message = _check_generic(check,
            input=t_obj.testcase_input_path,
            output=t_obj.testcase_output_path,
            judge=t_obj.testcase_expected_output_path,
            code_path=t_obj.submission_code_path,
            tc_id=t_obj.testcase_id,
            identical=t_obj.testcase_result,
        )
        r_obj.result = verdict == Verdict.AC
        r_obj.message = hr_verdict_name[verdict]

    if print_message and message:
        print(message, file=sys.stderr)
### @@ }

### @@if format in ('cms', 'cms-it') {
# CMS has a specific format in stdout and stderr, so we make it stricter
@_register_platform_checker('cms')
@_register_platform_checker('cms-it')
def _check_cms(check, *, score_file=sys.stdout, message_file=sys.stderr, title='', help=None, **kwargs):
    desc = help or CURR_PLATFORM + (' checker for the problem' + (f' "{title}"' if title else ''))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='input file path')
    parser.add_argument('judge_path', help='judge auxiliary data file path')
    parser.add_argument('output_path', help="contestant's file path")
    parser.add_argument('extra_args', nargs='*', help='extra arguments that will be ignored')
    # TODO check if this can receive force_verbose just like below
    args = parser.parse_args()

    verdict, score, message = _check_generic(check,
        input=args.input_path,
        output=args.output_path,
        judge=args.judge_path,
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

### @@if format == 'dom' {
@_register_platform_checker('dom')
def _check_dom(check, *, title='', log_file=sys.stdout, help=None, exit_after=True, **kwargs):
    desc = help or (CURR_PLATFORM + (' checker for the problem' + (f' "{title}"' if title else '')) +
            " (it takes the contestant's output file from stdin)")
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='input file path')
    parser.add_argument('judge_path', help='judge auxiliary data file path')
    parser.add_argument('feedback_dir', nargs='?', help='location to write auxiliary data to')
    parser.add_argument('extra_args', nargs='*', help='extra arguments that will be ignored')
    args = parser.parse_args()

    if args.extra_args:
        warn_print(f"Received extra args {args.extra_args}... ignoring them.", file=log_file)
    print(f"Checking the output...", file=log_file)

    verdict, score, message = _check_generic(check,
        input=args.input_path,
        output=(sys.stdin.name, sys.stdin),
        judge=args.judge_path,
        verbose=True,
    )

    print(f"Result:  {verdict}", file=log_file)
    print(f"Score:   {score}", file=log_file)
    if message: print(f"Message: {overflow_ell(message, 1000)}", file=log_file)

    exit_code = domjudge_rcode[verdict]
    if exit_after: exit(exit_code)

    return exit_code

### @@ }

### @@if format in ('local', 'kg', 'pg', 'pc2') {
@_register_platform_checker('local')
@_register_platform_checker('kg')
@_register_platform_checker('pg')
@_register_platform_checker('pc2')
def _check_local(check, *, title='', log_file=sys.stdout, help=None, force_verbose=False, exit_after=True):
    desc = help or CURR_PLATFORM + (' checker for the problem' + (f' "{title}"' if title else ''))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('input_path', help='input file path')
    parser.add_argument('output_path', help="contestant's file path")
    parser.add_argument('judge_path', help='judge auxiliary data file path')
    parser.add_argument('result_file', nargs='?', help='target file to contain the verdict in XML format')
    parser.add_argument('extra_args', nargs='*', help='extra arguments that will be ignored')
    parser.add_argument('-C', '--code', default='n/a', help='path to the solution used')
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
        if args.extra_args:
            warn_print(f"{tc_id:>3} [C] Received extra args {args.extra_args}... ignoring them.", file=log_file)
        print(f"{tc_id:>3} [C] Checking the output...", file=log_file)

    verdict, score, message = _check_generic(check,
        input=args.input_path,
        output=args.output_path,
        judge=args.judge_path,
        code_path=args.code,
        tc_id=args.tc_id,
        identical=args.identical,
        verbose=verbose,
    )

    if verbose:
        print(f"{tc_id:>3} [C] Result:  {verdict}", file=log_file)
        print(f"{tc_id:>3} [C] Score:   {score}", file=log_file)
        if message: print(f"{tc_id:>3} [C] Message: {overflow_ell(message, 100)}", file=log_file)
    else:
        print(f"{tc_id:>3} [C] Score={score} {verdict}", file=log_file)

    if args.result_file:
        if verbose: print(f"{tc_id:>3} [C] Writing result to '{args.result_file}'...", file=log_file)
        ### @@replace '_json_', '_json_' if format in ('local', 'kg') else '_xml_' {
        write_json_verdict(verdict, message, score, args.result_file)
        ### @@}

    if CURR_PLATFORM == 'pc2':
        exit_code = polygon_rcode[verdict]
    elif CURR_PLATFORM == 'pg':
        # assumes max score is 100. TODO learn what polygon really does
        exit_code = polygon_partial + int(score * 100) if 0 < score < 1 else polygon_rcode[verdict]
    else:
        exit_code = kg_rcode[verdict]

    if exit_after: exit(exit_code)

    return exit_code

### @@ }




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



# TODO argv thing
def check_files(check, *args, platform=CURR_PLATFORM, **kwargs):
    return _platform_checkers[platform](check, *args, **kwargs)



