from functools import wraps
from collections import deque
import re

from .utils import * ### @import



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
        '''
        Combine two Bounds objects together. Merges intervals for conflicting attributes.
        If not both are intervals, an error is raised.
        '''
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
def strict_int(x, *args):
    '''
    Check if the string x is a valid integer token, and that it satisfies certain constraints.

    Sample usage:
    strict_int(x) # just checks if the token is a valid integer.
    strict_int(x, 5) # checks if x is in the half-open interval [0, 5)
    strict_int(x, 5, 8) # checks if x is in the closed interval [5, 8]
    strict_int(x, interval) # check if  is in the Interval 'interval'
    '''
    if not _int_re.match(x):
        raise Exception("Expected integer literal, got: {}".format(repr(x)))
    x = int(x)
    if len(args) == 2:
        l, r = args
        if x not in Interval(l, r):
            raise Exception("Integer {} not in [{}, {}]".format(x, l, r))
    elif len(args) == 1:
        r, = args
        if isinstance(r, Interval):
            if x not in r:
                raise Exception("Integer {} not in {}".format(x, r))
        else:
            if x not in Interval(0, r - 1):
                raise Exception("Integer {} not in [0, {})".format(x, r))
    else:
        raise Exception("Invalid arguments to strict_int: {}".format(args))
    return x


class StrictStream(object):
    def __init__(self, file):
        self._last = None
        self._buff = deque()
        self.file = file

    # TODO add read_line

    @listify
    def read_ints(self, n, *args, **kwargs):
        sep = ''.join(kwargs.get('sep', ' '))
        for i in range(n):
            yield self.read_int(*args)
            if i < n - 1:
                for ch in sep:
                    self.read_char(ch)
        for ch in kwargs.get('end', ''):
            self.read_char(ch)

    def read_token(self, regex=None):
        tok = self._read_token()
        if regex is not None and not re.match('^' + regex + '$', tok):
            raise Exception("Expected token with regex {}, got {}".format(repr(regex), repr(tok)))
        return tok

    def read_int(self, *args):
        return strict_int(self.read_token(), *args)

    def read_space(self):
        return self.read_char(' ')

    def read_eoln(self):
        return self.read_char('\n') # ubuntu only (I think).

    def read_eof(self):
        return self.read_char(EOF)

    def read_char(self, ch):
        if self._next_char() != ch:
            raise Exception("Expected {}, got {}".format(self._label(ch), repr(self._last)))

    def _label(self, ch):
        if ch == EOF:
            return 'end-of-file'
        else:
            assert len(ch) == 1
            return repr(ch)

    # TODO learn how to buffer idiomatically...
    def _buffer(self):
        if not self._buff: self._buff += self.file.read(10**5) or [EOF]

    def _next_char(self):
        self._buffer()
        self._last = self._buff.popleft()
        return self._last

    def _peek_char(self):
        self._buffer()
        return self._buff[0]

    def _read_token(self):
        res = []
        while self._peek_char() not in [EOF, ' ', '\t', '\n']: res.append(self._next_char())
        return ''.join(res)
            
    # convenience
    def read_int_eoln(self, *args):
        res = self.read_int(*args); self.read_eoln()
        return res
    def read_int_space(self, *args):
        res = self.read_int(*args); self.read_space()
        return res
    def read_ints_eoln(self, *args):
        res = self.read_ints(*args); self.read_eoln()
        return res
    def read_ints_space(self, *args):
        res = self.read_ints(*args); self.read_space()
        return res
    def read_token_eoln(self, *args):
        res = self.read_token(*args); self.read_eoln()
        return res
    def read_token_space(self, *args):
        res = self.read_token(*args); self.read_space()
        return res

    @property
    def read(self):
        return _Read(self)

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

    def int(self, *args):
        def read_int(): yield self.ss.read_int(*args)
        return _Read(self.ss, self, read_int)

    def ints(self, *args):
        def read_ints(): yield self.ss.read_ints(*args)
        return _Read(self.ss, self, read_ints)

    def token(self, *args):
        def read_token(): yield self.ss.read_token(*args)
        return _Read(self.ss, self, read_token)

    def char(self, *args):
        def read_char():
            return self.ss.read_char(*args)
            yield
        return _Read(self.ss, self, read_char)

    @property
    def space(self): return self.char(' ')
    @property
    def eoln(self): return self.char('\n')
    @property
    def eof(self): return self.char(EOF)
    
    


def validator(f):
    @wraps(f)
    def new_f(file, *args, **kwargs):
        return f(StrictStream(file), *args, **kwargs)

    return new_f


