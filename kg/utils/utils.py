import functools
import os
import re

def noop(*args, **kwargs): ...

def abs_error(a, b):
    return abs(a - b)

def abs_rel_error(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1)

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
    def dec(f):
        @functools.wraps(f)
        def new_f(*args, **kwargs):
            return g(f(*args, **kwargs))
        return new_f
    if name is not None: dec.__name__ = name
    return dec

listify = apply_after(list, 'listify')


def memoize(function):
    memo = {}
    @functools.wraps(function)
    def f(*args, **kwargs):
        key = args, tuple(sorted(kwargs.items()))
        if key not in memo: memo[key] = function(*args, **kwargs)
        return memo[key]
    f.memo = memo
    return f

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


def file_sequence(s):
    if s.startswith(':'):
        for v in t_sequence(s[1:]):
            yield os.path.join('temp', str(v))
    else:
        yield from map(str, t_sequence(s))

def overflow_ell(s, ct):
    assert ct >= 3
    s = str(s)
    return s if len(s) <= ct else s[:ct-3] + '...'



def default_return(ret):
    def _default_return(f):
        @functools.wraps(f)
        def new_f(*args, **kwargs):
            res = f(*args, **kwargs)
            return res if res is not None else ret
        return new_f
    return _default_return

default_score = default_return(1.0)



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
