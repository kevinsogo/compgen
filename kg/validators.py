from collections import deque
from decimal import Decimal
from functools import wraps
from string import digits
from sys import stderr
import re

from .utils import * ### @import

CURR_PLATFORM = 'local' ### @replace 'local', format

class ValidationError(Exception): ...

class StreamError(ValidationError): ...

class VarMeta(type):
    def __pos__(self): return self()

class Var(metaclass=VarMeta):
    def __init__(self, *, pref='', lims=None):
        self.pref = pref
        self.lims = lims if lims is not None else []
        if any(isinstance(v, Var) for t, v in self.lims): raise TypeError("Operand cannot be Var")
        super().__init__()

    def add(self, t, v):
        if isinstance(v, Var): return NotImplemented
        try:
            append = self.lims.append
        except AttributeError:
            return NotImplemented
        append((self.pref + t, v))
        return self
    def __le__(self, v): return self.add('le', v)
    def __lt__(self, v): return self.add('lt', v)
    def __ge__(self, v): return self.add('ge', v)
    def __gt__(self, v): return self.add('gt', v)
    def __eq__(self, v): return self.add('eq', v)
    def __ne__(self, v): return self.add('ne', v)
    def __abs__(self): return Var(pref=self.pref+'abs ', lims=self.lims)

    def __and__(self, other):
        if not isinstance(other, Var): raise TypeError(f"Cannot merge {self.__class__.__name__} with {other.__class__.__name__}")
        return self.__class__(pref=self.pref, lims=self.lims+other.lims)
    # TODO implement __or__

    def __contains__(self, x):
        return all(self._satisfies(x, *c) for c in self.lims)

    @classmethod
    def _satisfies(cls, a, type, b):
        while type.startswith('abs '): type, a = type[4:], abs(a)
        if type == 'le': return a <= b
        if type == 'lt': return a < b
        if type == 'ge': return a >= b
        if type == 'gt': return a > b
        if type == 'eq': return a == b
        if type == 'ne': return a != b
        raise ValueError(f"Unknown type: {type}")

    def __repr__(self):
        return f'{self.__class__.__name__}(pref={self.pref!r}, lims={self.lims!r})'

    def __str__(self):
        try:
            res = self.compact_str()
        except Exception as exc:
            ...
        else:
            if res is not None: return res
        return self.raw_str()

    def compact_str(self):
        low = float('-inf'), +1
        hgh = float('+inf'), -1
        def add_cond(type, v):
            nonlocal low, hgh
            if type in ['le', 'lt']:
                hgh = min(hgh, (v, (0 if type == 'le' else -1)))
            elif type in ['ge', 'gt']:
                low = max(low, (v, (0 if type == 'ge' else +1)))
            else:
                raise ValueError(f"Unknown type: {type}")

        for type_, b in self.lims:
            absed = False
            while type_.startswith('abs '): type_, absed = type_[4:], True
            if type_ == 'eq' and not absed:
                add_cond('ge', b)
                add_cond('le', b)
            else:
                add_cond(type_, b)
                if absed:
                    if type_ == 'le':
                        add_cond('ge', -b)
                    elif type_ == 'lt':
                        add_cond('gt', -b)
                    else:
                        return

        lowv, lowt = low
        hghv, hght = hgh
        if lowv < hghv or lowv == hghv and lowt == hght == 0: return f"{'[('[lowt]}{lowv}, {hghv}{'])'[hght]}"
        return '(empty set)'

    def raw_str(self):
        def str_once(type, b):
            x = 'x'
            while type.startswith('abs '): type, x = type[4:], f'|{x}|'
            if type == 'le': return f"{x} <= {b}"
            if type == 'lt': return f"{x} < {b}"
            if type == 'ge': return f"{b} <= {x}"
            if type == 'gt': return f"{b} < {x}"
            if type == 'eq': return f"{x} == {b}"
            if type == 'ne': return f"{x} != {b}"
            raise ValueError(f"Unknown type: {type}")
        return "[Interval bounded by: {}]".format(', '.join(sorted(set(str_once(*x) for x in self.lims))) or 'none')

# TODO remove 'Interval' (backwards incompatible) ### @if False
def interval(l, r): return l <= +Var <= r
Interval = interval

EOF = ''

class Bounds:
    def __init__(self, bounds):
        self._attrs = []
        if bounds:
            for name, value in bounds.items():
                self._attrs.append(name)
                if isinstance(value, Var): value = Var(lims=tuple(value.lims)) # copy and freeze the Var
                setattr(self, name, value)
        super().__init__()

    def __and__(self, other):
        ''' Combine two Bounds objects together. Merges intervals for conflicting attributes.
        If not both are intervals, an error is raised. '''
        m = {}
        for attr in sorted(set(self._attrs) | set(other._attrs)):
            def combine(a, b):
                if a is None: return b
                if b is None: return a
                if isinstance(a, Var) and isinstance(b, Var): return a & b
                if not isinstance(a, Var) and not isinstance(b, Var): return b
                raise ValidationError(f"Conflict for attribute {attr} in merging!")
            m[attr] = combine(getattr(self, attr, None), getattr(other, attr, None))
        return Bounds(m)

    def __repr__(self):
        bounds = {attr: getattr(self, attr) for attr in self._attrs}
        return f'{self.__class__.__name__}({bounds!r})'

    def __str__(self):
        return '{{Bounds:\n{}}}'.format(''.join(f'\t{a}: {getattr(self, a)}\n' for a in self._attrs))


_int_re = re.compile(r'0|(?:-?[1-9]\d*)$')
intchars = set('-' + digits)
EOLN = '\n'

def strict_int(x, *args): ### @@ if False {
    ''' Check if the string x is a valid integer token, and that it satisfies certain constraints.

    Sample usage:
    strict_int(x) # just checks if the token is a valid integer.
    strict_int(x, 5) # checks if x is in the half-open interval [0, 5)
    strict_int(x, 5, 8) # checks if x is in the closed interval [5, 8]
    strict_int(x, interval) # check if  is in the Interval 'interval'
    '''
    ### @@ }
    if not _int_re.match(x):
        raise ValidationError(f"Expected integer literal, got: {x!r}")
    if args == ['str']: return x
    x = int(x)
    _check_range(x, *args, type="Integer")
    return x

def _check_range(x, *args, type="Number"):
    if len(args) == 2:
        l, r = args
        if not (l <= x <= r): raise ValidationError(f"{type} {x} not in [{l}, {r}]")
    elif len(args) == 1:
        if args[0] == 'str': return x
        r, = args
        if isinstance(r, Var):
            if x not in r: raise ValidationError(f"{type} {x} not in {r}")
        else:
            if not (0 <= x < r): raise ValidationError(f"{type} {x} not in [0, {r})")
    elif len(args) == 0:
        pass
    else:
        raise ValidationError(f"Invalid arguments for range check: {args}")
    return x

_real_re = re.compile(r'-?(?:0?|(?:[1-9]\d*))(?:\.\d*)?$')
_real_neg_zero_re = re.compile(r'-0(?:\.0*)')
realchars = intchars | {'.'}

def strict_real(x, *args, max_places=None, places=None, negzero=False, dotlead=False, dottrail=False): ### @@ if False {
    ''' Check if the string x is a valid real token, and that it satisfies certain constraints.

    It receives the same arguments as strict_int, and also receives the following in addition:

    places: If it is an integer, then x must have exactly 'places' after the decimal point.
    negzero: If True, then "negative zero", like, -0.0000, is not allowed. (default False)
    dotlead: If True, then a leading dot, like, ".420", is not allowed. (default False)
    dottrail: If True, then a trailing dot, like, "420.", is not allowed. (default False)
    '''
    ### @@ }
    if not _real_re.match(x) and x != '.':
        raise ValidationError(f"Expected real literal, got: {x!r}")
    if not negzero and _real_neg_zero_re.match(x):
        raise ValidationError(f"Real negative zero not allowed: {x!r}")
    if not dotlead and x.startswith('.'):
        raise ValidationError(f"Real with leading dot not allowed.")
    if not dottrail and x.endswith('.'):
        raise ValidationError(f"Real with trailing dot not allowed.")

    pl = len(x) - 1 - x.find('.')
    if max_places is not None:
        if pl > max_places: raise ValidationErrorf(f"Decimal place count of {x} exceeds {max_places}")

    if places is not None:
        pl = len(x) - 1 - x.index('.')
        if isinstance(places, Var):
            if pl not in Var: raise ValidationError(f"Decimal place count of {x} not in {places}")
        else:
            if pl != places: raise ValidationError(f"Decimal place count of {x} not equal to {places}")

    if args == ['str']: return x
    x = Decimal(x)
    _check_range(x, *args, type="Real")
    return x





_GET = None
### @@ if locals().get('WITH_GET', True) {
class _GET:
    def __add__(a, b): return _ADD(a, b)
    def __radd__(a, b): return _RADD(a, b)
    def __sub__(a, b): return _SUB(a, b)
    def __rsub__(a, b): return _RSUB(a, b)
    def __mul__(a, b): return _MUL(a, b)
    def __rmul__(a, b): return _RMUL(a, b)
    def __truediv__(a, b): return _TRUEDIV(a, b)
    def __rtruediv__(a, b): return _RTRUEDIV(a, b)
    def __floordiv__(a, b): return _FLOORDIV(a, b)
    def __rfloordiv__(a, b): return _RFLOORDIV(a, b)
    def __mod__(a, b): return _MOD(a, b)
    def __rmod__(a, b): return _RMOD(a, b)

class GET(_GET):
    def __init__(self, label):
        self.label = label
        super().__init__()

    def __call__(self, ss):
        return ss[self.label]

class _OP(_GET):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        super().__init__()

class _ADD(_OP):
    def __call__(g, ss): return ss._get(g.a)+ss._get(g.b)
class _SUB(_OP):
    def __call__(g, ss): return ss._get(g.a)-ss._get(g.b)
class _MUL(_OP):
    def __call__(g, ss): return ss._get(g.a)*ss._get(g.b)
class _TRUEDIV(_OP):
    def __call__(g, ss): return ss._get(g.a)/ss._get(g.b)
class _FLOORDIV(_OP):
    def __call__(g, ss): return ss._get(g.a)//ss._get(g.b)
class _MOD(_OP):
    def __call__(g, ss): return ss._get(g.a)%ss._get(g.b)

class _RADD(_OP):
    def __call__(g, ss): return ss._get(g.b)+ss._get(g.a)
class _RSUB(_OP):
    def __call__(g, ss): return ss._get(g.b)-ss._get(g.a)
class _RMUL(_OP):
    def __call__(g, ss): return ss._get(g.b)*ss._get(g.a)
class _RTRUEDIV(_OP):
    def __call__(g, ss): return ss._get(g.b)/ss._get(g.a)
class _RFLOORDIV(_OP):
    def __call__(g, ss): return ss._get(g.b)//ss._get(g.a)
class _RMOD(_OP):
    def __call__(g, ss): return ss._get(g.b)%ss._get(g.a)
### @@ }

SSBAD = object()

def charname(ch):
    if ch == SSBAD: return 'past-end-of-file'
    if ch == EOF: return 'end-of-file'
    assert len(ch) == 1
    return repr(ch)

def save_on_label(func):
    @wraps(func)
    def with_label(ss, *a, **kw):
        label = kw.pop('label', '')
        res = func(ss, *a, **kw)
        if label: ss._found[label] = res
        return res
    return with_label

class StrictStream:
    def __init__(self, file):
        self.last = None
        self.file = file
        self._buff = deque()
        self._found = {}
        super().__init__()

    def __getitem__(self, key):
        return self._found[key]

    def _get(self, key):
        return key(self) if isinstance(key, _GET) else key ### @ if locals().get('WITH_GET', True)
        return key ### @ if not locals().get('WITH_GET', True)

    # TODO learn how to buffer idiomatically...
    buffer_size = 10**5
    def _buffer(self):
        if not self._buff: self._buff += self.file.read(self.buffer_size) or [EOF, SSBAD]

    def _next_char(self):
        self._buffer()
        self.last = self._buff.popleft()
        if self.last is SSBAD: raise ValidationError("Read past EOF")
        return self.last

    def _peek_char(self):
        self._buffer()
        if self._buff[0] is SSBAD: raise ValidationError("Peeked past EOF")
        return self._buff[0]

    @save_on_label
    def read_until(self, ends, *, charset=(), n=None, maxn=None, include_end=False, _called="token"):
        ends = set(ends)
        n = self._get(n)
        maxn = self._get(maxn)
        if maxn is None: maxn = float('inf')
        if maxn < 0: raise ValueError(f"maxn must be nonnegative: {maxn}")
        charset = set(charset)
        res = []
        while self._peek_char() not in ends:
            if charset and self._peek_char() not in charset:
                raise StreamError(f"Invalid character for {_called} detected: {charname(self._peek_char())}")
            res.append(self._next_char())
            if n is not None and len(res) > n: raise StreamError(f"Expected exactly {n} characters, got more.")
            if len(res) > maxn: raise StreamError(f"Took too many characters! Expected at most {maxn}")
        if n is not None and len(res) != n: raise StreamError(f"Expected exactly {n} characters, got {len(res)}")
        if include_end: res.append(self._next_char())
        return ''.join(res)

    @save_on_label
    def read_line(self, *, eof=False, _called="line", **kwargs):
        return self.read_until([EOLN] + ([EOF] if eof else []), _called=_called, **kwargs)

    @save_on_label
    def read_token(self, regex=None, *, other_ends=[], _called="token", **kwargs): # optimize this. 
        tok = self.read_until([EOF, ' ', '\t', EOLN] + other_ends, _called=_called, **kwargs)
        if regex is not None and not re.match('^' + regex + '$', tok):
            raise StreamError(f"Expected token with regex {regex!r}, got {tok!r}")
        return tok

    @save_on_label
    @listify
    def do_multiple(self, f, count, *a, **kw):
        count = self._get(count)
        if count < 0: raise ValueError(f"n must be nonnegative: {count}")
        sep = ''.join(kw.pop('sep', ' '))
        end = kw.pop('end', '')
        for i in range(count):
            yield f(*a, **kw)
            if i < count - 1:
                for ch in sep: self.read_char(ch)
        for ch in end: self.read_char(ch)

    def read_ints(self, *a, **kw): return self.do_multiple(self.read_int, *a, **kw)
    def read_tokens(self, *a, **kw): return self.do_multiple(self.read_token, *a, **kw)
    def read_reals(self, *a, **kw): return self.do_multiple(self.read_real, *a, **kw)

    @save_on_label
    def read_int(self, *a, **kw):
        return strict_int(self.read_token(charset=intchars, _called="int"), *map(self._get, a), **kw)

    @save_on_label
    def read_real(self, *a, **kw):
        return strict_real(self.read_token(charset=realchars, _called="real"), *map(self._get, a), **kw)

    def read_space(self): return self.read_char(' ')
    def read_eoln(self): return self.read_char(EOLN) # ubuntu only (I think).
    def read_eof(self): return self.read_char(EOF)

    # TODO call this 'expect_char' (or something. check testlib. don't necessarily follow), and make _next_char public
    @save_on_label
    def read_char(self, ch):
        if self._next_char() != ch: raise StreamError(f"Expected {charname(ch)}, got {charname(self.last)}")

    # convenience
    def __getattr__(self, name):
        if not name.startswith('read_'): return
        for tail in ['_eoln', '_eof', '_space']:
            if name.endswith(tail):
                head = name[:-len(tail)]
                break
        else:
            raise AttributeError
        def convenience(self, *a, **kw):
            res = getattr(self, head)(*a, **kw)
            getattr(self, 'read' + tail)()
            return res
        convenience.__name__ = name
        setattr(self.__class__, name, convenience)
        return getattr(self, name)

    @property
    def read(self): return _Read(self)

# Chain validation:
class _Read:
    def __init__(self, ss, parent=None, op=None):
        self.ss = ss
        self.parent = parent
        self.op = op
        super().__init__()

    def __iter__(self):
        if self.parent: yield from self.parent
        if self.op: yield from self.op()

    def consume(self):
        return list(self)

    __call__ = consume

    def _make_chain(name):
        def chain(self, *a, **kw):
            def op(label=''): yield getattr(self.ss, 'read_' + name)(*a, **_add_label(kw, label))
            return _Read(self.ss, self, op)
        chain.__name__ = name
        return chain

    for _chain in ['line', 'int', 'ints', 'real', 'reals', 'token', 'tokens']:
        exec(f'{_chain} = _make_chain({_chain!r})') # evil hack for now

    del _make_chain, _chain

    def char(self, *a, **kw):
        def op():
            return self.ss.read_char(*a, **kw); yield
        return _Read(self.ss, self, op)

    def label(self, label):
        def nop(): return self.op(label=label)
        return _Read(self.ss, self.parent, nop)

    __getitem__ = label

    @property
    def space(self): return self.char(' ')
    @property
    def eoln(self): return self.char(EOLN) # ubuntu only (I think).
    @property
    def eof(self): return self.char(EOF)
    
def _add_label(kw, label):
    if label:
        if 'label' in kw: raise StreamError(f"Duplicate label: {label} {kw['label']}")
        kw['label'] = label
    return kw


def validator(*, suppress_eof_warning=False):
    def _validator(f):
        @wraps(f)
        def new_f(file, *args, **kwargs):
            sf = StrictStream(file)
            res = f(sf, *args, **kwargs)
            if sf.last != EOF and not suppress_eof_warning: print("Warning: The validator didn't check for EOF at the end.", file=stderr)
            ### @@ if format == 'pc2' {
            if CURR_PLATFORM == 'pc2':
                exit(42) # magic number to indicate successful validation (PC^2)
            ### @@ }
            return res
        return new_f
    return _validator
