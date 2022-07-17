import argparse, functools, io, itertools, re, sys

from .utils import * ### @import
from .utils.intervals import * ### @import
from .utils.parsers import * ### @import

_patterns = functools.lru_cache(maxsize=None)(re.compile)


class ValidationError(Exception): ...


# TODO needs unification with the other streams   ### @ if False
class StrictInputStream:
    def __init__(self, file, *, interactive=False):
        self.last = None
        self.next = None
        # NOTE: in the future, if we want to handle OS-based newlines, this step needs to be reconsidered
        if not interactive and not isinstance(file, io.StringIO):
            file = io.StringIO(file.read())
        self.file = file
        # self._found = {}  # TODO add labels
        self._read = ChainRead(self)
        super().__init__()

    @classmethod
    def from_string(self, s):
        return StrictInputStream(io.StringIO(s))

    # def __getitem__(self, key):
    #     return self._found[key]

    def _next_char(self):
        if self.last == EOF: raise StreamError("Read past EOF")
        if self.next is None: self.next = self.file.read(1)
        self.last = self.next
        self.next = None
        return self.last

    def peek_char(self):
        if self.last == EOF: raise StreamError("Peeked past EOF")
        if self.next is None: self.next = self.file.read(1)
        return self.next

    def _read_cond(self, good, bad, *, l=None, n=None, maxn=None, include_end=False, _called="_read_cond"):
        if maxn is None: maxn = (1 << 200) # 'infinite' enough for our purposes
        if l is not None:
            if not isinstance(l, Intervals):
                raise TypeError("Invalid type for l; must be intervals")
            maxn = int(min(maxn, l.upper_bound + 1))
        if maxn < 0:
            raise ValueError(f"maxn must be nonnegative; got {maxn}")
        res = io.StringIO()
        lres = 0
        while good(self.peek_char()):
            if bad(self.peek_char()):
                raise StreamError(f"Invalid character for {_called} detected: {stream_char_label(self.peek_char())}")
            res.write(self._next_char())
            lres += 1
            if n is not None and lres > n: 
                raise StreamError(f"Expected exactly {n} characters, got more.")
            if lres > maxn:
                raise StreamError(f"Took too many characters! Expected at most {maxn}")
        if n is not None and lres != n:
            raise StreamError(f"Expected exactly {n} characters, got {lres}")
        if l is not None and lres not in l:
            raise StreamError(f"Expected length in {l}, got {lres}")
        if include_end:
            res.write(self._next_char())
        return res.getvalue()

    def read_until(self, ends, *, other_ends=set(), charset=set(), _called="read_until", **kwargs):
        ends = force_to_set(ends)
        other_ends = force_to_set(other_ends)
        charset = force_to_set(charset)
        return self._read_cond(
            lambda ch: ch not in ends and ch not in other_ends,
            lambda ch: charset and ch not in charset,
            _called=_called,
            **kwargs,
        )

    def read_while(self, charset, *, ends=set(), _called="read_while", **kwargs):
        ends = force_to_set(ends)
        charset = force_to_set(charset)
        return self._read_cond(
            lambda ch: ch in charset,
            lambda ch: ch in ends,
            _called=_called,
            **kwargs,
        )

    def read_line(self, *, eof=False, _called="line", **kwargs):
        return self.read_until({EOLN, EOF} if eof else {EOLN}, _called=_called, **kwargs)

    def read_token(self, regex=None, *, ends={SPACE, EOLN, EOF}, other_ends=set(), _called="token", **kwargs): # optimize this. 
        tok = self.read_until(ends, other_ends=other_ends, _called=_called, **kwargs)
        if regex is not None and not _patterns('^' + regex + r'\Z').fullmatch(tok):
            raise StreamError(f"Expected token with regex {regex!r}, got {tok!r}")
        return tok

    @listify
    def _do_multiple(self, f, count, *a, **kw):
        if count < 0: raise ValueError(f"n must be nonnegative; got {count}")
        sep = kw.pop('sep', [SPACE])
        end = kw.pop('end', [])
        for i in range(count):
            yield f(*a, **kw)
            if i < count - 1:
                for ch in sep: self.read_char(ch)
        for ch in end: self.read_char(ch)

    def read_ints(self, *a, **kw): return self._do_multiple(self.read_int, *a, **kw)
    def read_tokens(self, *a, **kw): return self._do_multiple(self.read_token, *a, **kw)
    def read_reals(self, *a, **kw): return self._do_multiple(self.read_real, *a, **kw)


    def read_int(self, *args, **kwargs):
        # TODO use inspect.signature or something
        int_kwargs = {kw: kwargs.pop(kw) for kw in ('as_str',) if kw in kwargs}
        return strict_int(self.read_token(charset=intchars, _called="int", **kwargs), *args, **int_kwargs)

    def read_real(self, *args, **kwargs):
        # TODO use inspect.signature or something
        real_kwargs = {kw: kwargs.pop(kw) for kw in (
            'as_str', 'max_places', 'places', 'require_dot', 'allow_plus',
            'allow_neg_zero', 'allow_dot_lead', 'allow_dot_trail',
        ) if kw in kwargs}
        return strict_real(self.read_token(charset=realchars, _called="real", **kwargs), *args, **real_kwargs)

    def read_space(self): return self.read_char(SPACE)
    def read_eoln(self): return self.read_char(EOLN)
    def read_eof(self): return self.read_char(EOF)

    def read_char(self, target):
        if isinstance(target, str):
            if len(target) > 1:
                raise ValueError(f"Invalid argument for read_char: {target!r}")
            if self._next_char() != target:
                raise StreamError(f"Expected {stream_char_label(target)}, got {stream_char_label(self.last)}")
        else:
            target = force_to_set(target)
            if self._next_char() not in target:
                raise StreamError(f"Expected [{', '.join(map(stream_char_label, target))}], got {stream_char_label(self.last)}")
            return self.last

    # convenience
    # To implement read_int_eoln, read_real_space, read_int_space_space, etc.
    def __getattr__(self, name):
        if not name.startswith('read_'):
            raise AttributeError
        for tail in ['_eoln', '_eof', '_space']:
            if name.endswith(tail):
                head = name[:-len(tail)] # TODO removesuffix
                break
        else:
            raise AttributeError
        def _meth(self, *a, **kw):
            res = getattr(self, head)(*a, **kw)
            getattr(self, 'read' + tail)()
            return res
        _meth.__name__ = name # TODO setting __name__ doesn't seem to be enough
        setattr(self.__class__, name, _meth)
        return _meth

    @property
    def read(self):
        return self._read

StrictStream = StrictInputStream
# TODO add deprecation warnings? ### @if False


def validator(f=None, *, bounds=None, subtasks=None, extra_chars_allowed=False, suppress_eof_warning=None):
    ### @@ if False {
    if suppress_eof_warning is not None:
        warn("'suppress_eof_warning' is deprecated (and currently ignored); use 'extra_chars_allowed' instead")
    ### @@ }

    def _d(f):
        @functools.wraps(f)
        def _f(file, *args, force_subtask=False, interactive=False, **kwargs):
            if force_subtask and not (subtasks and 'subtask' in kwargs and kwargs['subtask'] in subtasks):
                raise RuntimeError(f"invalid subtask given: {kwargs.get('subtask')!r}")
            stream = StrictInputStream(file, interactive=interactive)
            if bounds is not None or subtasks is not None:
                lim = Bounds(kwargs.get('lim'))
                if bounds: lim &= Bounds(bounds)
                if subtasks: lim &= Bounds(subtasks.get(kwargs['subtask']))
                kwargs['lim'] = lim
            res = f(stream, *args, **kwargs)
            if stream.last != EOF and not extra_chars_allowed:
                stream.read_eof()
            ### @@ if format == 'pc2' {
            if CURR_PLATFORM == 'pc2':
                exit(42) # magic number to indicate successful validation (PC^2)
            ### @@ }
            return res
        return _f

    return _d(f) if f is not None else _d

def detect_subtasks(validate, file, subtasks, *args, **kwargs):
    file = io.StringIO(file.read())
    for subtask in subtasks:
        try:
            file.seek(0)
            validate(file, *args, subtask=subtask, force_subtask=True, **kwargs)
        except Exception:
            ... 
        else:
            yield subtask

def validate_or_detect_subtasks(validate, subtasks, file=sys.stdin, outfile=sys.stdout, *args, title='', **kwargs):
    desc = CURR_PLATFORM + ' validator for the problem' + (f' "{title}"' if title else '')
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('subtask', nargs='?', help='which subtask to check the file against')
    parser.add_argument('--detect-subtasks', '-d', action='store_true', help='detect subtasks instead')
    pargs, unknown = parser.parse_known_args()
    subtask = pargs.subtask

    ### @@ if format != 'pg' {
    # suppress error messages when uploaded to Polygon
    if subtask is not None and subtask not in subtasks:
        # we need to allow invalid subtasks because Polygon passes some arguments to the validator
        # TODO actually learn the arguments that Polygon actually passes
        raise ValidationError("Invalid subtask name.")
    ### @@ }

    if pargs.detect_subtasks:
        print(*detect_subtasks(validate, file, subtasks, *args, **kwargs), file=outfile)
    else:
        validate(file, *args, subtask=subtask, **kwargs)

