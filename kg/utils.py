from functools import wraps
from itertools import islice
import os.path
import re


def noop(*args, **kwargs): ...

def abs_error(a, b):
    return abs(a - b)

def abs_rel_error(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1)

def ensure(condition, message=None, exc=Exception):
    ''' assert that doesn't raise AssertionError. Useful/Convenient for judging. '''
    if not condition:
        try:
            message = message()
        except TypeError:
            ...
        if isinstance(message, str):
            message = exc(message)
        raise message or exc()


def apply_after(g, name=None):
    ''' Make a decorator that applies "g" to the return value of a function. '''
    def dec(f):
        @wraps(f)
        def new_f(*args, **kwargs):
            return g(f(*args, **kwargs))
        return new_f
    if name is not None: dec.__name__ = name
    return dec

listify = apply_after(list, 'listify')


def memoize(function):
    memo = {}
    @wraps(function)
    def f(*args, **kwargs):
        key = args, tuple(sorted(kwargs.items()))
        if key not in memo: memo[key] = function(*args, **kwargs)
        return memo[key]
    f.memo = memo
    return f

inf = 10**18
r_int = r'0|(?:-?[1-9]\d*)'
r_sint = r'[+-](?:0|(?:[1-9]\d*))'

patterns = [
    rf'(?P<start>{r_int})(?:(?:\.\.)|-)(?P<end>{r_int})\((?P<step>{r_sint})\)',
    rf'(?P<start>{r_int})(?:(?:\.\.)|-)(?P<end>{r_int})',
    rf'(?P<start>{r_int})\((?P<step>{r_sint})\)',
    rf'(?P<start>{r_int})',
]

patterns = [re.compile('^' + pat + '$') for pat in patterns]

def _t_range_args(s):
    for pat in patterns:
        m = pat.match(s)
        if m:
            m = m.groupdict()
            start = int(m['start'])
            step = int(m.get('step', 1))
            if 'end' in m:
                end = int(m['end'])
                if step < 0: end -= 1
                if step > 0: end += 1
            elif 'step' in m:
                if step < 0:
                    end = -inf
                elif step > 0:
                    end = +inf
                else:
                    end = None
            else:
                assert step == 1
                end = start + 1
            if step and end is not None and (end - start) * step >= 0:
                return start, end, step
    raise ValueError(f"Range cannot be read: {repr(s)}")

def t_range(r):
    return range(*_t_range_args(r))

def t_infinite(r):
    start, end, step = _t_range_args(r)
    return abs(end) >= inf


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

def file_sequence(s):
    if s.startswith(':'):
        for v in t_sequence(s[1:]):
            yield os.path.join('temp', str(v))
    else:
        yield from t_sequence(s)

### @@ if False {
# TODO make unit tests
# print(list(islice(t_sequence('2'), 100)))
# print(list(islice(t_sequence('12'), 100)))
# print(list(islice(t_sequence('-2'), 100)))
# print(list(islice(t_sequence('3,5-7,11'), 100)))
# print(list(islice(t_sequence('3,5-7,9..11'), 100)))
# print(list(islice(t_sequence('3,5-7,9..11,15(+1)'), 100)))
# print(list(islice(t_sequence('3,5-7,9..11,15(+2)'), 100)))
# print(list(islice(t_sequence('5(+2)'), 100)))
# print(list(islice(t_sequence('5..19(+2)'), 100)))
### @@ }
