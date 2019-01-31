from collections import deque
from functools import wraps
from string import digits
from sys import stderr
import re

from .utils import * ### @import

class ValidationError(Exception): ...

class StreamError(ValidationError): ...

class Interval:
    ''' Represents a closed interval [l, r] '''
    def __init__(self, l, r):
        self.l = l
        self.r = r
        super(Interval, self).__init__()

    def __and__(self, other):
        if not isinstance(other, Interval): raise TypeError("Cannot merge {} with {}".format(self.__class__.__name__, other.__class__.__name__))
        return Interval(max(self.l, other.l), min(self.r, other.r))

    def __len__(self):
        return max(0, self.r - self.l + 1)

    def __contains__(self, x):
        return self.l <= x <= self.r

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, repr(self.l), repr(self.r))

    def __str__(self):
        return '[{}, {}]'.format(self.l, self.r)


EOF = ''

class Bounds:
    def __init__(self, bounds):
        self._attrs = []
        if bounds:
            for name, value in bounds.items():
                self._attrs.append(name)
                setattr(self, name, value)
        super(Bounds, self).__init__()

    def __and__(self, other):
        ''' Combine two Bounds objects together. Merges intervals for conflicting attributes.
        If not both are intervals, an error is raised. '''
        m = {}
        for attr in sorted(set(self._attrs) | set(other._attrs)):
            def combine(a, b):
                if a is None: return b
                if b is None: return a
                if not (isinstance(a, Interval) and isinstance(b, Interval)):
                    raise Exception("Conflict for attribute {} in merging!".format(attr))
                return a & b
            m[attr] = combine(getattr(self, attr, None), getattr(other, attr, None))
        return Bounds(m)


_int_re = re.compile(r'0|(?:-?[1-9]\d*)$')
intchars = set('-' + digits)

def strict_int(x, *args):
    ''' Check if the string x is a valid integer token, and that it satisfies certain constraints.

    Sample usage:
    strict_int(x) # just checks if the token is a valid integer.
    strict_int(x, 5) # checks if x is in the half-open interval [0, 5)
    strict_int(x, 5, 8) # checks if x is in the closed interval [5, 8]
    strict_int(x, interval) # check if  is in the Interval 'interval'
    '''
    if not _int_re.match(x):
        raise Exception("Expected integer literal, got: {}".format(repr(x)))
    if len(args) == 2:
        x = int(x)
        l, r = args
        if not (l <= x <= r):
            raise Exception("Integer {} not in [{}, {}]".format(x, l, r))
    elif len(args) == 1:
        if args[0] == 'str': return x
        x = int(x)
        r, = args
        if isinstance(r, Interval):
            if x not in r:
                raise Exception("Integer {} not in {}".format(x, r))
        else:
            if not (0 <= x < r):
                raise Exception("Integer {} not in [0, {})".format(x, r))
    else:
        raise Exception("Invalid arguments to strict_int: {}".format(args))
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
        super(GET, self).__init__()

    def __call__(self, ss):
        return ss[self.label]

class _OP(_GET):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        super(_OP, self).__init__()

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

BAD = object()

def charname(ch):
    if ch == BAD: return 'past-end-of-file'
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

class StrictStream(object):
    def __init__(self, file):
        self.last = None
        self.file = file
        self._buff = deque()
        self._found = {}

    def __getitem__(self, key):
        return self._found[key]

    def _get(self, key):
        return key(self) if isinstance(key, _GET) else key ### @ if locals().get('WITH_GET', True)
        return key ### @ if not locals().get('WITH_GET', True)

    # TODO learn how to buffer idiomatically...
    def _buffer(self):
        if not self._buff: self._buff += self.file.read(10**5) or [EOF, BAD]

    def _next_char(self):
        self._buffer()
        self.last = self._buff.popleft()
        if self.last is BAD: raise ValidationError("Read past EOF")
        return self.last

    def _peek_char(self):
        self._buffer()
        if self._buff[0] is BAD: raise ValidationError("Peeked past EOF")
        return self._buff[0]

    @save_on_label
    def read_until(self, ends, charset=None, maxn=None, include_end=False):
        maxn = self._get(maxn)
        if maxn is None: maxn = float('inf')
        if maxn < 0: raise ValueError("maxn must be nonnegative: {}".format(maxn))
        if not isinstance(charset, set): charset = set(charset or ())
        res = []
        while self._peek_char() not in ends:
            if charset and self._peek_char() not in charset: raise StreamError("Invalid character detected: {}".format(charname(self._peek_char())))
            if len(res) >= maxn: raise StreamError("Took too many characters! Expected at most {}".format(maxn))
            res.append(self._next_char())
        if include_end: res.append(self._next_char())
        return ''.join(res)

    @save_on_label
    def read_line(self, eof=False, maxn=None, include_end=False):
        return self.read_until(['\n'] + ([EOF] if eof else []), maxn=maxn, include_end=include_end)

    @save_on_label
    def read_token(self, charset=None, regex=None, maxn=None, other_ends=[], include_end=False): # optimize this. 
        tok = self.read_until([EOF, ' ', '\t', '\n'] + other_ends, charset=charset, maxn=maxn, include_end=include_end)
        if regex is not None and not re.match('^' + regex + '$', tok):
            raise StreamError("Expected token with regex {}, got {}".format(repr(regex), repr(tok)))
        return tok

    @save_on_label
    @listify
    def do_multiple(self, f, n, *a, **kw):
        n = self._get(n)
        if n < 0: raise ValueError("n must be nonnegative: {}".format(n))
        sep = ''.join(kw.get('sep', ' '))
        for i in range(n):
            yield f(*a)
            if i < n - 1:
                for ch in sep: self.read_char(ch)
        for ch in kw.get('end', ''): self.read_char(ch)

    def read_ints(self, *a, **kw): return self.do_multiple(self.read_int, *a, **kw)
    def read_tokens(self, *a, **kw): return self.do_multiple(self.read_token, *a, **kw)

    @save_on_label
    def read_int(self, *a, **kw):
        return strict_int(self.read_token(charset=intchars), *map(self._get, a))

    def read_space(self): return self.read_char(' ')
    def read_eoln(self): return self.read_char('\n') # ubuntu only (I think).
    def read_eof(self): return self.read_char(EOF)

    # TODO call this 'expect_char' (or something. check testlib. don't necessarily follow), and make _next_char public
    @save_on_label
    def read_char(self, ch):
        if self._next_char() != ch:
            raise StreamError("Expected {}, got {}".format(charname(ch), charname(self.last)))

    # convenience
    def read_int_eoln(self, *a, **kw):
        res = self.read_int(*a, **kw); self.read_eoln(); return res
    def read_int_space(self, *a, **kw):
        res = self.read_int(*a, **kw); self.read_space(); return res
    def read_ints_eoln(self, *a, **kw):
        res = self.read_ints(*a, **kw); self.read_eoln(); return res
    def read_ints_space(self, *a, **kw):
        res = self.read_ints(*a, **kw); self.read_space(); return res
    def read_token_eoln(self, *a, **kw):
        res = self.read_token(*a, **kw); self.read_eoln(); return res
    def read_token_space(self, *a, **kw):
        res = self.read_token(*a, **kw); self.read_space(); return res
    def read_tokens_eoln(self, *a, **kw):
        res = self.read_tokens(*a, **kw); self.read_eoln(); return res
    def read_tokens_space(self, *a, **kw):
        res = self.read_tokens(*a, **kw); self.read_space(); return res

    @property
    def read(self): return _Read(self)

# Chain validation:
class _Read:
    def __init__(self, ss, parent=None, op=None):
        self.ss = ss
        self.parent = parent
        self.op = op
        super(_Read, self).__init__()

    def __iter__(self):
        if self.parent:
            yield from self.parent
        if self.op:
            yield from self.op()

    def int(self, *a, **kw):
        def op(label=''): yield self.ss.read_int(*a, **_add_label(kw, label))
        return _Read(self.ss, self, op)

    def ints(self, *a, **kw):
        def op(label=''): yield self.ss.read_ints(*a, **_add_label(kw, label))
        return _Read(self.ss, self, op)

    def token(self, *a, **kw):
        def op(label=''): yield self.ss.read_token(*a, **_add_label(kw, label))
        return _Read(self.ss, self, op)

    def tokens(self, *a, **kw):
        def op(label=''): yield self.ss.read_tokens(*a, **_add_label(kw, label))
        return _Read(self.ss, self, op)

    def char(self, *a, **kw):
        def op():
            return self.ss.read_char(*a, **kw)
            yield
        return _Read(self.ss, self, op)

    def label(self, label):
        def nop(): return self.op(label=label)
        return _Read(self.ss, self.parent, nop)

    __getitem__ = label

    @property
    def space(self): return self.char(' ')
    @property
    def eoln(self): return self.char('\n')
    @property
    def eof(self): return self.char(EOF)
    
def _add_label(kw, label):
    if label:
        if 'label' in kw: raise StreamError("Duplicate label: {} {}".format(label, kw['label']))
        kw['label'] = label
    return kw


def validator(suppress_eof_warning=False):
    def _validator(f):
        @wraps(f)
        def new_f(file, *args, **kwargs):
            sf = StrictStream(file)
            res = f(sf, *args, **kwargs)
            if sf.last != EOF and not suppress_eof_warning: print("Warning: The validator didn't check for EOF at the end.", file=stderr)
            return res
        return new_f
    return _validator
