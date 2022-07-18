import argparse, contextlib, functools, io, json, sys, traceback

from .utils import * ### @import
from .utils.streams import * ### @import
from .utils.judging import * ### @import


class InteractorError(Exception): ...


class Interactor:
    def __call__(self, input_file, *users, output_file, judge_file=None, **kwargs):
        with contextlib.ExitStack() as stack:
            input_s = stack.enter_context(InteractiveStream(
                input_file,
                mode=ISMode(self.input_mode),
                exc=lambda message: Fail(f'[input] {message}'),
                **self.stream_settings['input'],
            ))
            # enable line buffering for all writers
            for user in users:
                user.writer.reconfigure(line_buffering=True)
            user_ss = [
                stack.enter_context(InteractiveStream(
                    user.reader,
                    user.writer,
                    mode=ISMode(self.from_user_mode),
                    exc=lambda message: ParseError(f'[user {userid}] {message}'),
                    **self.stream_settings['user'],
                )) for userid, user in enumerate(users)
            ]
            output_s = stack.enter_context(InteractiveStream(
                None,
                output_file,
                exc=lambda message: Fail(f'[output] {message}'),
            ))
            judge_s = stack.enter_context(InteractiveStream(
                judge_file,
                mode=ISMode(self.judge_mode),
                exc=lambda message: Fail(f'[judge] {message}'),
                **self.stream_settings['judge'],
            )) if judge_file else None

            return self.interact(input_s, *user_ss, output_stream=output_s, judge_stream=judge_s, **kwargs)

    def init(self, *args, **kwargs):
        # parse options ### @rem

        # TODO use kwargs for these...? ### @rem
        if not args: args = ['lines']
        if len(args) == 1: args = args*3
        if len(args) != 3: raise ValueError(f"Invalid args: {args}")
        self.input_mode, self.from_user_mode, self.judge_mode = args

        valid_fields = {'input', 'user', 'judge'}
        def to_fields(arg):
            value = kwargs.pop(arg, False)
            value = {*value} if not isinstance(value, bool) else valid_fields if value else set()
            if not value <= valid_fields:
                raise ValueError(f"Invalid {arg} argument(s): {value - valid_fields}")
            return value

        kwargs.setdefault('extra_chars_allowed', {'input', 'judge'})

        ### @@ rem {
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
        def _interactor(f):
            interact = cls()
            interact.interact = f
            interact.init(*args, **kwargs)
            return interact
        return _interactor(f) if f is not None else _interactor


# hmm, this is almost like just a dataclass ### @rem
class BuiltInteractor(Interactor):
    _names = {'get_one_input', 'get_judge_data_for_input', 'aggregate', 'iterate', 'interact_one', 'wrap_up'}
    _aliases = {}
    def __init__(self):
        for name in self._names: setattr(self, name, None)
        super().__init__()

    def init(self, *args, cases=None, **kwargs):
        if cases is None:
            pass
        elif cases == 'multi':
            self._set('iterate', interactor_iterate_with_casecount)
        elif cases == 'single':
            self._set('iterate', interactor_iterate_single)
        else:
            raise ValueError(f"Unknown 'cases' argument: {cases}")
        super().init(*args, **kwargs)

    def _set(self, name, arg):
        if name in self._aliases:
            name, wrong_name = self._aliases[name], name
            warn_deprec_name(wrong_name, name) ### @rem
        if name not in self._names:
            raise ValueError(f"Unknown name to set: {name}")
        if getattr(self, name):
            raise ValueError(f"{name} already set!")
        setattr(self, name, arg)
        return arg

    def interact(self, *args, **kwargs):
        return InteractionContext(self, *args, **kwargs)()


class InteractionContext:
    def __init__(self, interactor, input_stream, *users, output_stream, **kwargs):
        self.interactor = interactor
        self.input_stream = input_stream
        self.users = users
        self.output_stream = output_stream
        self.kwargs = kwargs
        super().__init__()

    @on_exhaust(Fail("Input stream fully read but expected more"))
    def get_one_input(self, **kwargs):
        return self.interactor.get_one_input(self.input_stream, output_stream=self.output_stream, exc=Fail, **kwargs, **self.kwargs)

    @on_exhaust(Fail("Judge data stream fully read but expected more"))
    def get_judge_data_for_input(self, input, **kwargs):
        if not self.interactor.get_judge_data_for_input: return
        return self.interactor.get_judge_data_for_input(self.kwargs.get('judge_stream'), input, output_stream=self.output_stream, exc=Fail, **kwargs, **self.kwargs)

    @on_exhaust(Fail("aggregate function failed"))
    def aggregate(self, scores):
        return (self.interactor.aggregate or minimum_score)(scores)

    @on_exhaust(Fail("iterate function failed"))
    def iterate(self):
        return (self.interactor.iterate or interactor_iterate_with_casecount)(self)

    @on_exhaust(Fail("interact_one function failed"))
    def interact_one(self, input, **kwargs):
        return self.interactor.interact_one(input, *self.users, output_stream=self.output_stream, **kwargs, **self.kwargs)

    @on_exhaust(Fail("wrap_up function failed"))
    def wrap_up(self, success, score, raised_exc, **kwargs):
        if not self.interactor.wrap_up: return
        return self.interactor.wrap_up(success, *self.users, output_stream=self.output_stream, score=score, raised_exc=raised_exc, **kwargs, **self.kwargs)

    def __call__(self):
        # will only wrap up on success or on Wrong/ParseError. ### @rem
        try:
            score = self.aggragate(self.iterate())
        except (Wrong, ParseError) as exc:
            self.wrap_up(success=False, score=None, raised_exc=exc)
            raise
        else:
            new_score = self.wrap_up(success=True, score=score, raised_exc=None)
            return new_score if new_score is not None else score


def make_interactor_builder():
    return Builder(name='interactor', build_standalone=Interactor.from_func, build_from_parts=BuiltInteractor)


interactor = make_interactor_builder()



def interactor_iterate_with_casecount(it):
    t = int(next(it.input_stream))
    for cas in range(t):
        inp = it.next_input(caseno=cas)
        yield it.interact_one(inp,
            judge_data=it.get_judge_data_for_input(inp, caseno=cas),
            caseno=cas,
        )


def interactor_iterate_single(it, *, cas=0):
    inp = it.next_input(caseno=cas)
    yield it.interact_one(inp,
        judge_data=it.get_judge_data_for_input(inp, caseno=cas),
        caseno=cas,
    )







def _interact_generic(interactor, input, *users, output=None, judge=None, **kwargs):
    def handle(exc, verdict):
        if kwargs.get('verbose'): traceback.print_exc(limit=None) ### @replace None, -1
        return verdict, getattr(exc, 'score', 0.0), str(exc)

    with contextlib.ExitStack() as stack:

        def maybe_open(arg, *args, **kwargs):
            if arg is None:
                return None, None
            elif isinstance(arg, str):
                return arg, stack.enter_context(open(arg, *args, **kwargs))
            elif hasattr(arg, 'name'):
                return arg.name, arg
            else:
                return arg

        kwargs['input_path'],  input_f  = maybe_open(input)
        kwargs['output_path'], output_f = maybe_open(output, 'w')
        kwargs['judge_path'],  judge_f  = maybe_open(judge)

        ### @@ rem {
        # open reads before writes first...
        # this is somewhat a fragile 'agreement' between the mediator (KompGen) and this interactor
        # however, opening FIFOs in nonblocking mode seem like such a hassle...
        # TODO really think about the best way to do this...
        ### @@ }
        fr_users_info = [maybe_open(fr_user) for fr_user, to_user in users]
        to_users_info = [maybe_open(to_user, 'w', buffering=1) for fr_user, to_user in users]
        (
            kwargs['from_user_paths'],
            kwargs['to_user_paths'],
            user_ios,
        ) = zip(*((
            fr_user_path,
            to_user_path,
            TextIOPair(fr_user, to_user),
        ) for userid, ((fr_user_path, fr_user), (to_user_path, to_user)) in enumerate(zip(fr_users_info, to_users_info))))

        try:
            score = interactor(input_f, *user_ios, output_file=output_f, judge_file=judge_f, **kwargs)
            if not (0.0 <= score <= 1.0):
                raise InteractorError(f"The interactor returned an invalid score: {score!r}")
            return Verdict.AC, score, ""
        except ParseError as exc:
            return handle(exc, Verdict.PAE)
        except Wrong as exc:
            return handle(exc, Verdict.WA)
        except Fail as exc:
            return handle(exc, Verdict.FAIL)
        except Exception as exc:
            return handle(exc, Verdict.EXC)







### @@ rem {


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


### @@ }


_plat_interactors = {}
def _reg_plat_interactor(name):
    def reg(f):
        assert name not in _plat_interactors, f"{name} registered twice!"
        _plat_interactors[name] = f
        return f
    return reg


### @@if format in ('cms', 'cms-it') {
# TODO check if this works
@_reg_plat_interactor('cms')
@_reg_plat_interactor('cms-it')
def _interact_cms(interact, *, input_file=sys.stdin, score_file=sys.stdout, message_file=sys.stderr, title='', help=None, **kwargs):
    desc = help or CURR_PLATFORM + (' interactor for the problem' + (f' "{title}"' if title else ''))
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('user_paths', nargs='*', help='paths to the pairs of files/FIFOs from and to each user')
    args = parser.parse_args()

    fr_users, to_users = args.user_paths[::2], args.user_paths[1::2]
    if len(fr_users) != len(to_users): raise InteractorError("Invalid number of arguments: must be even")

    if fr_users:
        users = [*zip(fr_users, to_users)]
    else:
        users = [(sys.stdin, sys.stdout)]

    verdict, score, message = _interact_generic(interact, input_file, *users, verbose=False)

    # TODO deliberate failure here if verdict is EXC, FAIL, or something ### @rem

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


# TODO the 'pg' version should maybe be stricter than this? ### @rem

### @@ if format in ('local', 'kg', 'pg') {
@_reg_plat_interactor('local')
@_reg_plat_interactor('pg')
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
        if args.extra_args: 
            warn_print(f"{tc_id:>3} [I] Received extra args {args.extra_args}... ignoring them.", file=log_file)
        print(f"{tc_id:>3} [I] Interacting with the solution...", file=log_file)

    if args.from_user or args.to_user:
        if not (args.from_user and args.to_user and len(args.from_user) == len(args.to_user)):
            raise InteractorError("There must be the same number of input and output files/FIFOs.")
        users = [*zip(args.from_user, args.to_user)]
    else:
        users = [(sys.stdin, sys.stdout)]

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
        exit_code = polygon_partial + int(score * 100) if 0 < score < 1 else polygon_rcode[verdict]
    else:
        exit_code = kg_rcode[verdict]

    if exit_after:
        exit(exit_code)

    return exit_code
### @@ }





# TODO argv thing
def interact_with(interact, *args, platform=CURR_PLATFORM, **kwargs):
    return _plat_interactors[platform](interact, *args, **kwargs)


