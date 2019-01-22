#!/usr/bin/python2

'''
Useful stuff for generating data, validating, etc.
'''

from __future__ import print_function

# @@@@@ embedding starts here

__author__ = "Kevin Atienza"
__license__ = "MIT"

__maintainer__ = "Kevin Atienza"
__email__ = "kevin.charles.atienza@gmail.com"
__status__ = "Development"
__version__ = "0.1"

import re
from StringIO import StringIO
from random import Random
from functools import wraps
from collections import deque



def ensure(condition, message=None):
    ''' assert that doesn't raise AssertionError. Useful/Convenient for judging. '''
    if not condition:
        try:
            message = message()
        except TypeError:
            pass
        raise Exception(message)


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


@listify
def group_into(v, seq):
    ''' Group 'seq' into lists of size "v". The last group could have size < v '''
    buf = []
    for s in seq:
        buf.append(s)
        ensure(len(buf) <= v, lambda: "v cannot be zero if seq is nonempty")
        if len(buf) == v:
            yield buf
            buf = []
    if buf:
        yield buf


class XRandom(Random):
    def shuff(self, x):
        x = list(x)
        self.shuffle(x)
        return x


# some hash on a sequence of integers. Don't change this! This is used by seed computation based on command line args.  
_pmod = 2013265921
_pbase = 1340157138
_xmod = 10**9 + 7
_xbase = 790790578
_xor = 0xDEAFBEEFEE
def _chash_seq(seq):
    pol = 0
    xol = 0
    for s in seq:
        pol = (pol * _pbase + s) % _pmod
        xol = ((xol * _xbase + s) ^ _xor) % _xmod
    return (pol << 32) ^ xol


class Interval(object):
    ''' Represents a closed interval [l, r] '''
    def __init__(self, l, r):
        self.l = l
        self.r = r
        super(Interval, self).__init__()

    def __and__(self, other):
        ensure(isinstance(other, Interval))
        return Interval(max(self.l, other.l), min(self.r, other.r))

    def __len__(self):
        return max(0, self.r - self.l + 1)

    def __contains__(self, x):
        return self.l <= x <= self.r

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, repr(self.l), repr(self.r))

    def __str__(self):
        return '[{}, {}]'.format(self.l, self.r)


class Bounds(object):
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
                ensure(isinstance(a, Interval) and isinstance(b, Interval), lambda: "Conflict for attribute {} in merging!".format(attr))
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
    ensure(_int_re.match(x), lambda: "Expected integer literal, got: {}".format(repr(x)))
    x = int(x)
    if len(args) == 2:
        l, r = args
        ensure(x in Interval(l, r), lambda: "Integer {} not in [{}, {}]".format(x, l, r))
    elif len(args) == 1:
        r, = args
        if isinstance(r, Interval):
            ensure(x in r, lambda: "Integer {} not in {}".format(x, r))
        else:
            ensure(x in Interval(0, r + 1), lambda: "Integer {} not in [0, {})".format(x, r))
    else:
        ensure(False, lambda: "Invalid arguments to strict_int: {}".format(args))
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
        for i in xrange(n):
            yield self.read_int(*args)
            if i < n - 1:
                for ch in sep:
                    self.read_char(ch)
        for ch in kwargs.get('end', ''):
            self.read_char(ch)

    def read_token(self, regex=None):
        tok = self._read_token()
        if regex is not None: ensure(re.match('^' + regex + '$', tok), lambda: "Expected token with regex {}, got {}".format(repr(regex), repr(tok)))
        return tok

    def read_int(self, *args):
        return strict_int(self.read_token(), *args)

    def read_space(self):
        return self.read_char(' ')

    def read_eoln(self):
        return self.read_char('\n') # ubuntu only (I think).

    def read_eof(self):
        return self.read_char('')

    def read_char(self, ch):
        ensure(self._next_char() == ch, lambda: "Expected {}, got {}".format(self._label(ch), repr(self._last)))

    def _label(self, ch):
        if ch == '':
            return 'end-of-file'
        else:
            assert len(ch) == 1
            return repr(ch)

    # TODO learn how to buffer idiomatically...
    def _buffer(self):
        if not self._buff: self._buff += self.file.read(10**5) or ['']

    def _next_char(self):
        self._buffer()
        self._last = self._buff.popleft()
        return self._last

    def _peek_char(self):
        self._buffer()
        return self._buff[0]

    def _read_token(self):
        res = []
        while self._peek_char() not in ['', ' ', '\t', '\n']: res.append(self._next_char())
        return ''.join(res)
            

def validator(f):
    @wraps(f)
    def new_f(file, *args, **kwargs):
        return f(StrictStream(file), *args, **kwargs)

    return new_f


def _write_with_validate(print_to_file, file, case_, validate=None):
    if validate is not None:
        tfile = StringIO()
        print_to_file(tfile, case_)
        validate(StringIO(tfile.getvalue())) # TODO can one read AND write on the same StringIO file?
        file.write(tfile.getvalue())
    else:
        print_to_file(file, case_)


def _make_seed(args):
    return _chash_seq(_chash_seq(map(ord, arg)) for arg in args) ^ 0xBEABDEEF


def write_to_file(print_to_file, make, args, file, validate=None):
    '''
    Creates test case/s meant for a single file.

    print_to_file: function that prints to a file
    make: function that generates the data
    args: arguments that will be passed to 'make', along with a random number generator.
    file: file-like object to write to.
    validate: (optional) Validate the output before printing

    Note: Ensure that `make` is deterministic, and any "randomness" is obtained from
    the given random number generator. This ensures reproducibility.
    '''
    rand = XRandom(_make_seed(args))
    case_ = make(rand, *args)
    _write_with_validate(print_to_file, file, case_, validate=validate)


def _get_all_groups(make, distribute, args):
    # make the cases
    rand = XRandom(_make_seed(args))
    casemakers = []
    def mnew_case(*fwd_args, **info):
        def _mnew_case(f):
            nrand_seed = rand.getrandbits(64) ^ 0xC0BFEFE
            @wraps(f)
            def new_f(): # now new_f is deterministic
                return f(XRandom(nrand_seed), *fwd_args)
            casemakers.append(new_f)
            mnew_case.total_cases += 1
            for name, value in info.items(): # forward any info
                setattr(new_f, name, value)
        return _mnew_case
    mnew_case.total_cases = 0
    make(rand, mnew_case, *args)

    # distribute
    def dnew_case(*fwd_args, **info):
        def _dnew_case(f):
            nrand_seed = rand.getrandbits(64) ^ 0xC0BFEFE
            @wraps(f)
            def new_f(): # now new_f is deterministic
                return f(XRandom(nrand_seed), *fwd_args)
            for name, value in info.items(): # forward any info
                setattr(new_f, name, value)
            return new_f
        return _dnew_case
    return distribute(rand, dnew_case, casemakers, *args)


def write_nth_group_to_file(index, print_to_file, make, distribute, args, file, validate=None):
    '''
    Creates test case/s meant for several files, and returns the 'index'th among them. The given
    new_case decorator provides a way to ensure that only the needed cases are generated.

    print_to_file: function that prints to a file
    make: function that generates the data
    distribute: function that groups the data into separate files.
    args: arguments that will be passed to 'make', along with a random number generator.
    file: file-like object to write to.
    validate: (optional) Validate the output before printing

    Note: Ensure that `make` and `distribute` are deterministic, and any "randomness" is obtained from
    the given random number generator. This ensures reproducibility.
    '''
    groups = _get_all_groups(make, distribute, args)
    ensure(0 <= index < len(groups), lambda: "Invalid index: {} out of {} groups".format(index, len(groups)))
    group = [make() for make in groups[index]]
    _write_with_validate(print_to_file, file, group, validate=validate)
    return len(groups)
