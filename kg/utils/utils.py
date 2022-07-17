import collections, functools, os, os.path, pathlib, re, sys

warn_print = print

def noop(*a, **kw): ...


def warn_print(*a, **kw):
    if not warn_print.wp:
        try:
            from kg.script.utils import warn_print as _wp
        except ImportError:
            warn_print.wp = print
        else:
            warn_print.wp = _wp

    return warn_print.wp(*a, **kw)
warn_print.wp = None

warn = noop
### @@ if False {
def warn(warning):
    warn_print("WARNING:", warning, file=sys.stderr)
### @@ }


CURR_PLATFORM = 'local' ### @replace 'local', format or 'local'



def abs_error(a, b):
    return abs(a - b)

def abs_rel_error(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1)

def overflow_ell(s, ct=50, etc='...'):
    assert len(etc) <= ct
    s = str(s)
    return s if len(s) <= ct else s[-len(etc):] + etc

def ensure(condition, message="ensure condition failed. (see Traceback to determine which one)", exc=Exception):
    ''' assert that doesn't raise AssertionError. Useful/Convenient for judging. '''
    if not condition:
        try:
            message = message()
        except TypeError:
            ...
        if isinstance(message, str):
            message = exc(message)
        raise message or exc


def apply_after(g, name=None):
    ''' Make a decorator that applies "g" to the return value of a function. '''
    def _d(f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            return g(f(*args, **kwargs))
        return _f
    if name is not None: _d.__name__ = name
    return _d

listify = apply_after(list, 'listify')

memoize = functools.lru_cache(maxsize=None)

t_inf = 10**18
r_int = r'0|(?:-?[1-9]\d*)'
r_sint = r'[+-](?:0|(?:[1-9]\d*))'

t_patterns = [re.compile(rf'^{pat}\Z') for pat in [
    rf'(?P<start>{r_int})(?P<range>(?:\.\.)|-)(?P<end>{r_int})\((?P<step>{r_sint})\)',
    rf'(?P<start>{r_int})(?P<range>(?:\.\.)|-)(?P<end>{r_int})',
    rf'(?P<start>{r_int})(?P<range>\.\.)\((?P<step>{r_sint})\)',
    rf'(?P<start>{r_int})(?P<range>\.\.)',
    rf'(?P<start>{r_int})',
]]

def _t_range_args(s, *, inf=t_inf, patterns=t_patterns):
    for pat in patterns:
        m = pat.match(s)
        if m:
            m = m.groupdict()
            start = int(m['start'])
            if m.get('range'):
                step = int(m.get('step', 1))
                if 'end' in m:
                    end = int(m['end'])
                    if step < 0: end -= 1
                    if step > 0: end += 1
                else:
                    if step < 0:
                        end = -inf
                    elif step > 0:
                        end = +inf
                    else:
                        end = None
            else:
                step = 1
                end = start + 1
            if step and end is not None and (end - start) * step >= 0:
                return start, end, step
    raise ValueError(f"Range cannot be read: {s!r}")

def t_range(r, *, inf=t_inf):
    return range(*_t_range_args(r, inf=inf))

def t_infinite(r, *, inf=t_inf):
    start, end, step = _t_range_args(r, inf=inf)
    return abs(end) >= inf

### @@ if False {
# TODO TSequence class
# iterable, also supports indexing
# TSequence.ranges
# TSequence.compress
### @@ }
def t_sequence_ranges(s):
    return [t_range(p) for p in s.split(',')]

def t_sequence(s):
    for r in s.split(','):
        yield from t_range(r)

@listify
def list_t_sequence(s):
    for r in s.split(','):
        if t_infinite(r):
            raise ValueError(f"Cannot form a list from an infinite range {r}")
        yield from t_range(r)

def compress_t_sequence(s, *, inf=t_inf):
    def exactize(start, end, step):
        return start, end + (start - end) % step, step
    def decode(r):
        return exactize(*_t_range_args(r, inf=inf))
    @listify
    def combine_ranges(a, b):
        astart, aend, astep = a
        bstart, bend, bstep = b
        if astep == bstep and aend == bstart:
            yield astart, bend, astep
        else:
            yield from (a, b)
    def merge_ranges(ranges1, ranges2):
        *ranges1, erange1 = ranges1
        frange2, *ranges2 = ranges2
        return list(ranges1) + combine_ranges(erange1, frange2) + list(ranges2)
    def encode(start, end, step):
        assert (end - start) % step == 0
        end = '' if abs(end) >= inf else end - step
        if end != '': assert (end - start) * step >= 0
        if start == end:
            return str(start)
        else:
            assert step
            step_sgn = '+' if step > 0 else '-' if step < 0 else '?'
            step_str = '' if step == 1 else f'({step_sgn}{abs(step)})'
            range_ = '..' if end == '' else '-'
            return f'{start}{range_}{end}{step_str}'
    return ','.join(encode(*t) for t in functools.reduce(merge_ranges, ([decode(r)] for r in s.split(','))))


def file_sequence(s, *, mktemp=False):
    if s.startswith(':'):
        if mktemp:
            print("Ensuring the 'temp' folder exists...", file=sys.stderr) ### @if False
            pathlib.Path('temp').mkdir(parents=True, exist_ok=True)
        for v in t_sequence(s[1:]):
            yield os.path.join('temp', str(v))
    else:
        yield from map(str, t_sequence(s))


def default_return(ret):
    def _d(f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            res = f(*args, **kwargs)
            return res if res is not None else ret
        return _f
    return _d

default_score = default_return(1.0)

### @@ if False {
# def merge_dicts(d, *others, duplicates='error'):
#     if duplicates not in {'error', 'first', 'last'}:
#         raise ValueError(f"Invalid 'duplicates' argument: {duplicates!r}")
#     d = d.copy()
#     for o in others:
#         for k, v in o.items():
#             if k not in d:
#                 d[k] = v
#             elif duplicates == 'error':
#                 raise ValueError(f"duplicate key: {k!r}")
#             elif duplicates == 'first':
#                 pass
#             elif duplicates == 'last':
#                 d[k] = v
#             else:
#                 raise Exception
#     return d
### @@ }


EOF = ''
EOLN = '\n'
SPACE = ' '

def stream_char_label(ch):
    if ch == EOF: return 'end-of-file'
    assert len(ch) == 1
    return repr(ch)

def force_to_set(s):
    if not isinstance(s, collections.Set):
        s = frozenset(s)
        ### @@if False {
        if not force_to_set.warned:
            force_to_set.warned = True
            warn_print(
                    "Note: I recommend passing a set as arguments "
                    "(e.g., to charset, ends, other_ends, token_ends, read_char) "
                    "to make things a bit faster",
                    file=sys.stderr)
        ### @@}
    return s

force_to_set.warned = False ### @if False



class Builder:
    def __init__(self, name, build_standalone, build_from_parts):
        self.name = name
        self.build_standalone = build_standalone
        self.build_from_parts = build_from_parts
        self.pending = None
        super().__init__()

    def start_building(self):
        if self.pending is None: self.pending = self.build_from_parts()
        return self.pending

    def set(self, arg):
        self.start_building()
        if callable(arg):
            try:
                name = arg.__name__
            except AttributeError:
                ...
            else:
                return self._set(name, arg)

        return functools.partial(self._set, arg)

    def _set(self, name, arg):
        self.start_building()
        return self.pending._set(name, arg)

    def make(self, *args, **kwargs):
        if self.pending is None: raise RuntimeError("Cannot build: no .set done. Did you mean @checker?")

        # get additional stuff from kwargs
        for name in self.pending._names:
            if name in kwargs: self._set(name, kwargs.pop(name))

        interact = self.pending
        self.pending = None
        interact.init(*args, **kwargs)
        return interact

    def __call__(self, *args, **kwargs):
        if self.pending is not None: raise RuntimeError(f"Cannot build standalone {self.name} if .set has been done. Did you mean to call .make?")
        return self.build_standalone(*args, **kwargs)



def warn_on_call(warning):
    _d = lambda f: f
    ### @@ if False {
    def _d(f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            if not _f.called:
                _f.called = True
                warn(warning)
            return f(*args, **kwargs)
        _f.__wrapped__ = f
        _f.called = False
        return _f
    ### @@ }
    return _d

def deprec_name_warning(*a, **kw): return '!'
warn_deprec_name = noop
def deprec_alias(oname, nobj, *a, **kw): return nobj

### @@ if False {
def deprec_name_warning(old_name, new_name):
    return f"{new_name!r} deprec; use {old_name!r} instead"

def warn_deprec_name(old_name, new_name):
    warn(deprec_name_warning(old_name, new_name))

def deprec_alias(old_name, new_obj, new_name=None):
    if new_name is None: new_name = new_obj.__name__
    warner = warn_on_call(deprec_name_warning(old_name, new_name))
    # guess what this object is
    if callable(new_obj):
        new_obj = warner(new_obj)
    else:
        new_obj.__getattr__ = warner(new_obj.__getattr__)
    return new_obj
### @@ }


# Chain validation
class ChainRead:
    def __init__(self, stream):
        self._s = stream
        self._r = collections.deque()
        super().__init__()

    def __iter__(self):
        while self._r:
            yield self._r.popleft()

    def __call__(self): return list(self)

    ### @@if False {
    # TODO __getitem__ to label the last result.
    # must not exist among the named variables in Bounds
    # must not label the same value more than once
    # a label can change value.
    ### @@}

    def line(self, *a, **kw):
        self._r.append(self._s.read_line(*a, **kw)); return self

    def int(self, *a, **kw):
        self._r.append(self._s.read_int(*a, **kw)); return self

    def ints(self, *a, **kw):
        self._r.append(self._s.read_ints(*a, **kw)); return self

    def real(self, *a, **kw):
        self._r.append(self._s.read_real(*a, **kw)); return self

    def reals(self, *a, **kw):
        self._r.append(self._s.read_reals(*a, **kw)); return self

    def token(self, *a, **kw):
        self._r.append(self._s.read_token(*a, **kw)); return self

    def tokens(self, *a, **kw):
        self._r.append(self._s.read_tokens(*a, **kw)); return self

    def until(self, *a, **kw):
        self._r.append(self._s.read_until(*a, **kw)); return self

    def while_(self, *a, **kw):
        self._r.append(self._s.read_while(*a, **kw)); return self

    def char(self, *a, **kw):
        res = self._s.read_char(*a, **kw)
        if res is not None: self._r.append(res)
        return self

    @property
    def space(self):
        self._s.read_space(); return self

    @property
    def eoln(self):
        self._s.read_eoln(); return self

    @property
    def eof(self):
        self._s.read_eof(); return self

    @property
    def spaces(self):
        self._s.read_spaces(); return self


def pop_callable(s):
    f = None
    if len(s) >= 1 and callable(s[0]): f, *s = s
    return f, s


### @@ if False {
if __name__ == '__main__':
    # TODO make proper unit tests
    from itertools import islice
    print(list(islice(t_sequence('2'), 100)))
    print(list(islice(t_sequence('12'), 100)))
    print(list(islice(t_sequence('-2'), 100)))
    print(list(islice(t_sequence('3,5-7,11'), 100)))
    print(list(islice(t_sequence('3,5-7,9..11'), 100)))
    print(list(islice(t_sequence('3,5-7,9..11,15..(+1)'), 100)))
    print(list(islice(t_sequence('3,5-7,9..11,15..(+2)'), 100)))
    print(list(islice(t_sequence('5..'), 100)))
    print(list(islice(t_sequence('5..(+2)'), 100)))
    print(list(islice(t_sequence('5..19(+2)'), 100)))
    def check_compress(s):
        t = compress_t_sequence(s)
        print('we got', s, t, len(s) - len(t))
        assert list(islice(t_sequence(s), 10000)) == list(islice(t_sequence(s), 10000))

    check_compress('2')
    check_compress('2,5,3,4,5')
    check_compress('2,5,3,4,5,6..(+1)')
    check_compress('2,5,3,4,5,6..(-1)')
    check_compress('2,5,3,4,5,6..(-1),7-9,10-15,16')
    from random import Random
    rand = Random(11)
    def rand_range(V, inf=False):
        start = rand.randint(-V, V)
        if not inf and rand.random() < 0.2:
            return str(start)
        else:
            range_ = '..' if inf or rand.randrange(2) else '-'
            while True:
                end = rand.randint(-V, V)
                if start != end: break
            step = rand.randint(1, abs(start - end) + 1)
            if end < start: step = -step
            if inf: end = ''
            step_sgn = '+' if step > 0 else ''
            step_str = f'({step_sgn}{step})' if step != 1 or rand.randrange(2) else ''
            return f'{start}{range_}{end}{step_str}'

    for it in range(111111):
        last_inf = rand.randrange(2)
        V = rand.randint(1, 111) if rand.randrange(2) else rand.randint(1, 11)
        partc = rand.randint(0, 21)
        s = ','.join([rand_range(V) for i in range(partc)] + [rand_range(V, inf=last_inf)])
        check_compress(s)


### @@ }
