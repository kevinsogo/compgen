import collections, enum, functools, io

from .parsers import * ### @import
from .utils import * ### @import

class StreamError(Exception): ...
class NoLineError(StreamError): ...
class NoTokenError(StreamError): ...
class NoCharError(StreamError): ...

class ISMode(enum.Enum):
    LINES = 'lines'
    TOKENS = 'tokens'
    RAW_LINES = 'raw_lines'

ISTREAM_DEFAULTS = {
    'extra_chars_allowed': False,
    'ignore_blank_lines': False,
    'ignore_trailing_blank_lines': False,
    'require_trailing_eoln': False,
    'parse_validate': False,
    'line_include_ends': False,
    'line_ignore_trailing_spaces': False,
    'token_skip_spaces': False,
    'token_skip_eolns': False,
    'eoln_skip_spaces': False,
}

ISTREAM_MODE_DEFAULTS = {
    ISMode.LINES: {
        'ignore_trailing_blank_lines': True,
        'line_ignore_trailing_spaces': True,
        'eoln_skip_spaces': True,
    },
    ISMode.TOKENS: {
        'ignore_blank_lines': True,
        'ignore_trailing_blank_lines': True,
        'line_ignore_trailing_spaces': True,
        'token_skip_spaces': True,
        'token_skip_eolns': True,
        'eoln_skip_spaces': True,
    },
    ISMode.RAW_LINES: {
        'line_include_ends': True,
    },
}


class IStreamState:
    def __init__(self, file, *, exc=StreamError):
        self._file = file
        self._exc = exc
        # this ought to be a deque, but collections.deque doesn't have random access ### @rem
        self._buf = ['']
        self._l = 0
        self._i = 0
        self._future1 = None
        self._future2 = None
        super().__init__()

    def next_line(self):
        if self.remaining(): raise RuntimeError("Cannot get buffer next line if not all characters in the current line have been consumed")
        self._l += 1
        self._i = 0
        if self._l == len(self._buf):
            try:
                line = self._file.readline()
            except UnicodeDecodeError as ex:
                raise self._exc("Output stream is not properly encoded") from ex
            else:
                self._buf.append(line)
        if self._future2 is not None and self._future1 != (self._l, self._i):
            self._future1 = None
            self._future2 = None
        if self._future1 is None: self._drop_lines()
        return self._buf[self._l]

    def remaining(self):
        return len(self._buf[self._l]) - self._i

    def peek(self):
        if not self.remaining(): raise RuntimeError("Cannot peek buffer if all characters in the current line have been consumed")
        return self._buf[self._l][self._i]

    def advance(self):
        if not self.remaining(): raise RuntimeError("Cannot advance buffer if all characters in the current line have been consumed")
        self._i += 1

    def consume_line(self):
        buf = self._buf[self._l]
        line = buf[self._i:]
        self._i = len(buf)
        return line

    def consume_until(self, ends):
        i = self._i
        buf = self._buf[self._l]
        while self._i < len(buf) and buf[self._i] not in ends: self._i += 1
        return buf[i:self._i]

    _DROP = 64
    def _drop_lines(self):
        if self._DROP < len(self._buf) < 2 * self._l:
            self._buf = self._buf[self._l:]
            self._l = 0

    def future_begin(self):
        self._drop_lines()
        self._future1 = (self._l, self._i)
        self._future2 = None

    def future_cancel(self):
        (self._l, self._i) = self._future1
        self._future1 = None
        self._future2 = None
        self._drop_lines()

    def future_freeze(self):
        if not (self._future1 and not self._future2):
            raise RuntimeError("Cannot freeze future if it has not yet begun")
        self._future2 = (self._l, self._i)
        (self._l, self._i) = self._future1

    def future_commit(self):
        if not (self._future1 and self._future2):
            raise RuntimeError("Cannot commit future if the future state hasn't been frozen")

        if (self._l, self._i) != self._future1:
            raise RuntimeError("Cannot commit future if the state has changed since the last freeze")

        (self._l, self._i) = self._future2
        self._future1 = None
        self._future2 = None
        self._drop_lines()

### @@rem {
# TODO I ought to make this a subclass of TextIOBase or something, but please read about its implications
# I think the default .readline implementation calls .read somehow, but we're repurposing .read here
### @@}
class InteractiveStream:
    def __init__(self, reader, writer=None, *, mode=None, exc=StreamError, **options):
        if reader and not reader.readable(): raise OSError('"reader" argument must be writable')
        if writer and not writer.writable(): raise OSError('"writer" argument must be writable')
        if mode is not None and not isinstance(mode, ISMode): raise ValueError(f"Invalid InteractiveStream mode: {mode}")

        self._reader = reader
        self.writer = writer
        self._mode = mode
        self.exc = exc

        # global defaults ### @rem
        self._opts = {**ISTREAM_DEFAULTS}

        # mode defaults ### @rem
        if self._mode is not None:
            self._opts.update(ISTREAM_MODE_DEFAULTS[self._mode])

        # overwritten options ### @rem
        self._opts.update(options)

        self._token_ends = {SPACE, EOLN}
        self._closed = False
        self._pending = None

        self._buf = IStreamState(self._reader, exc=exc) if self._reader else None
        self._read = ChainRead(self)

        super().__init__()

    @property
    def reader(self): return self._reader

    def _check_open(self):
        if self._closed: raise RuntimeError("InteractiveStream is closed")

    def __iter__(self): return self

    def __next__(self):
        self._check_open()

        # if there's a pending thing, just return that and commit the future ### @rem
        if self._pending is not None:
            res = self._pending
            self._pending = None
            self._buf.future_commit()
            return res

        if self._mode == ISMode.TOKENS:
            try:
                return self.read_token(exc=NoTokenError)
            except NoTokenError as ex:
                raise StopIteration from ex
        else:
            try:
                return self.read_line(exc=NoLineError)
            except NoLineError as ex:
                raise StopIteration from ex

    def has_next(self):
        self._check_open()
        try:
            self.peek()
        except StopIteration:
            return False
        else:
            return True

    def peek(self):
        self._check_open()
        if self._pending is None:
            self._buf.future_begin()
            try:
                self._pending = next(self)
            except:
                assert self._pending is None
                self._buf.future_cancel()
                raise
            else:
                assert self._pending is not None
                self._buf.future_freeze()
        return self._pending

    def __enter__(self):
        self._check_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._check_open()
        self.close(exc_type=exc_type)

    def close(self, *, exc_type=None):
        if self._closed: return
        self._pending = None

        try:
            if self.reader and exc_type is None and not self._opts['extra_chars_allowed']:
                if self._opts['ignore_blank_lines'] or self._opts['ignore_trailing_blank_lines']:
                    while True:
                        if self._buf.remaining():
                            try:
                                self._read_eoln_or_eof(exc=NoCharError)
                            except NoCharError as ex:
                                raise self.exc("Extra nonempty lines found at the end") from ex
                        if not self._buffer_line():
                            break
                elif self._buf.remaining() or self._buffer_line():
                    raise self.exc("Extra characters found at the end")
        finally:
            try:
                if self.writer: self.writer.close()
            except BrokenPipeError: # silently allow broken pipe errors
                pass
            finally:
                self._closed = True # can only set this after closing

    def _buffer_line(self):
        buf = self._buf.next_line()
        if self._opts['require_trailing_eoln'] and buf and not buf.endswith(EOLN):
            raise self.exc(f"trailing {stream_char_label(EOLN)} not found")
        return buf

    def read_line(self, *, include_ends=None, ignore_trailing_spaces=None, exc=None):
        self._check_open()
        self._pending = None

        if include_ends is None:
            include_ends = self._opts['line_include_ends']
        if ignore_trailing_spaces is None:
            ignore_trailing_spaces = self._opts['line_ignore_trailing_spaces']
        if include_ends and ignore_trailing_spaces:
            raise ValueError("Cannot ignore trailing spaces if include_ends is true")

        while True:
            if not self._buf.remaining() and not self._buffer_line(): raise (exc or self.exc)("no line found")

            line = self._buf.consume_line()
            assert line

            if line == EOLN and self._opts['ignore_blank_lines']: continue

            # remove undesired trailing whitespace
            if not include_ends:
                last = len(line)
                if last and line[last - 1] == EOLN: last -= 1
                if ignore_trailing_spaces:
                    while last and line[last - 1] == SPACE: last -= 1
                line = line[:last]

            return line

    def read_token(self, *, l=None, ends=None, skip_spaces=None, skip_eolns=None, exc=None):
        self._check_open()
        self._pending = None

        if ends is None:
            ends = self._token_ends
        if skip_spaces is None:
            skip_spaces = self._opts['token_skip_spaces']
        if skip_eolns is None:
            skip_eolns = self._opts['token_skip_eolns']

        ends = force_to_set(ends)

        if not self._buf.remaining(): self._buffer_line()

        # skip whitespace ### @rem
        while self._buf.remaining() and (
            skip_spaces and self._buf.peek() == SPACE or
            skip_eolns  and self._buf.peek() == EOLN):
            self._buf.advance()
            if not self._buf.remaining(): self._buffer_line()

        # everything skipped ### @rem
        if not self._buf.remaining(): raise (exc or self.exc)("no token found")

        res = self._buf.consume_until(ends)
        if l is not None and len(res) not in l: raise self.exc(f"token too long! length must be in {l}")
        return res


    def read_spaces(self):
        self._check_open()
        self._pending = None
        
        while self._buf.remaining() and self._buf.peek() == SPACE: self._buf.advance()


    def read_char(self, target, *, skip_spaces=False, exc=None):
        self._check_open()
        self._pending = None

        if skip_spaces: self.read_spaces()

        if isinstance(target, str):
            if len(target) > 1: raise ValueError(f"Invalid argument for read_char: {target!r}")
            target = {target}
            ret = False
        else:
            target = force_to_set(target)
            ret = True

        if not self._buf.remaining(): self._buffer_line()
        ch = self._buf.peek() if self._buf.remaining() else EOF
        if ch not in target:
            raise (exc or self.exc)(f"{{{', '.join(map(stream_char_label, target))}}} expected but {stream_char_label(ch)} found")

        # advance only after successfully reading char ### @rem
        if ch != EOF: self._buf.advance()

        if ret: return ch

    def _read_eoln_or_eof(self, exc=None):
        return self.read_char({EOLN, EOF}, skip_spaces=self._opts['eoln_skip_spaces'], exc=exc)

    def read_eoln(self, *, skip_spaces=None, exc=None):
        if skip_spaces is None: skip_spaces = self._opts['eoln_skip_spaces']
        return self.read_char(EOLN, skip_spaces=skip_spaces, exc=exc)

    def read_eof(self, *, skip_spaces=None, exc=None):
        if skip_spaces is None: skip_spaces = self._opts['eoln_skip_spaces']
        return self.read_char(EOF, skip_spaces=skip_spaces, exc=exc)

    def read_space(self, exc=None):
        self.read_char(SPACE, exc=exc)


    @listify
    def _do_multiple(self, f, count, *a, cexc=None, **kw):
        if count < 0: raise ValueError(f"n must be nonnegative; got {count}")
        sep = kw.pop('sep', [SPACE])
        end = kw.pop('end', [])
        for i in range(count):
            yield f(*a, **kw)
            if i < count - 1:
                for ch in sep: self.read_char(ch, exc=cexc)
        for ch in end: self.read_char(ch, exc=cexc)

    def read_ints(self, *a, **kw): return self._do_multiple(self.read_int, *a, **kw)
    def read_tokens(self, *a, **kw): return self._do_multiple(self.read_token, *a, **kw)
    def read_reals(self, *a, **kw): return self._do_multiple(self.read_real, *a, **kw)


    def read_int(self, *args, validate=None, **kwargs):
        if validate is None: validate = self._opts['parse_validate']

        # TODO use inspect.signature or something ### @rem
        int_kwargs = {kw: kwargs.pop(kw) for kw in ('as_str',) if kw in kwargs}
        try:
            return strict_int(self.read_token(**kwargs), *args, validate=validate, **int_kwargs)
        except ParsingError as ex:
            raise self.exc(f"Cannot parse token to int: {', '.join(ex.args)}") from ex


    def read_real(self, *args, validate=None, **kwargs):
        if validate is None: validate = self._opts['parse_validate']

        # TODO use inspect.signature or something ### @rem
        real_kwargs = {kw: kwargs.pop(kw) for kw in (
            'as_str', 'max_places', 'places', 'require_dot', 'allow_plus', 'allow_neg_zero',
            'allow_dot_lead', 'allow_dot_trail',
        ) if kw in kwargs}
        try:
            return strict_real(self.read_token(**kwargs), *args, validate=validate, **real_kwargs)
        except ParsingError as ex:
            raise self.exc(f"Cannot parse token to real: {', '.join(ex.args)}") from ex


    # Convenience, to implement read_int_eoln, read_real_space, read_int_space_space, etc. ### @rem
    def __getattr__(self, name):
        if not name.startswith('read_'):
            raise AttributeError(name)
        for tail in ['_eoln', '_eof', '_space', '_spaces']:
            if name.endswith(tail):
                head = name[:-len(tail)] # TODO removesuffix
                break
        else:
            raise AttributeError(name)
        def _meth(self, *a, **kw):
            res = getattr(self, head)(*a, **kw)
            getattr(self, 'read' + tail)()
            return res
        # TODO setting __name__ doesn't seem to be enough. __qualname__ too? ### @rem
        _meth.__name__ = name
        setattr(self.__class__, name, _meth)
        return _meth

    @property
    def read(self): return self._read


    # stuff for the writer part follows ### @rem

    def write(self, *args): return self.writer.write(*args)

    def readable(self, *args):
        ### @@ rem {
        # this refers to the IOBase argument.
        # we don't want them to read from the stream the usual way since we have
        # our own layer of buffering
        ### @@ }
        return False

    def writable(self, *args): return self.writer.writable(*args)
    def flush(self, *args): return self.writer.flush(*args)
    def isatty(self): return self._reader.isatty() or self.writer.isatty()

    @property
    def closed(self): return self._closed

    @property
    def encoding(self): return self.writer.encoding

    @property
    def errors(self): return self.writer.errors

    @property
    def newlines(self): return self.writer.newlines

    def print(self, *args, **kwargs):
        kwargs.setdefault('file', self.writer)
        return print(*args, **kwargs)




class TextIOPair(io.TextIOBase): ### @@ rem {
    """
    Like BufferedRWPair, but:
    - takes in two text I/Os rather than raw I/Os
    - makes seekable() false
    #
    I tried to use TextIOWrapper(BufferedRWPair(...)), but I couldn't get it to work in some instances,
    particularly when both arguments are stdin and stdout, and stdin is piped from a file. (It seems the
    decoder.reset() call drops some data.) If you can get this working, feel free to replace this with that.
    #
    After some more investigation, this looks like an unfixed Python bug:
    https://github.com/python/cpython/issues/56424
    unfixed because "nobody complained about it for the last 9 years" :(
    #
    Relevant "decoder.reset()" call:
    https://github.com/python/cpython/blob/ca308c13daa722f3669a14f1613da768086beb6a/Modules/_io/textio.c#L1695
    https://github.com/python/cpython/blob/cceac5dd06fdbaba3f45b8be159dfa79b74ff237/Lib/_pyio.py#L2214
    """
    ### @@ }

    def __init__(self, reader, writer):
        if not reader.readable(): raise OSError('"reader" argument must be readable')
        if not writer.writable(): raise OSError('"writer" argument must be writable')
        self.reader = reader
        self.writer = writer
        super().__init__()

    def read(self, *args): return self.reader.read(*args)
    def readline(self, *args): return self.reader.readline(*args)
    def write(self, *args): return self.writer.write(*args)
    def peek(self, *args): return self.reader.peek(*args)
    def readable(self, *args): return self.reader.readable(*args)
    def writable(self, *args): return self.writer.writable(*args)
    def flush(self, *args): return self.writer.flush(*args)

    def close(self):
        try:
            self.writer.close()
        finally:
            self.reader.close()

    def isatty(self): return self.reader.isatty() or self.writer.isatty()

    @property
    def closed(self): return self.writer.closed
    @property
    def encoding(self): return self.writer.encoding
    @property
    def errors(self): return self.writer.errors
    @property
    def newlines(self): return self.writer.newlines

    def print(self, *args, **kwargs):
        kwargs.setdefault('file', self.writer)
        kwargs.setdefault('flush', True)
        return print(*args, **kwargs)

    def input(self): return self.readline().removesuffix('\n')
    
    def __iter__(self): return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line





### @@rem {
def test_some_stuff():
    import io, itertools







    class TEST_IStreamState:
        def __init__(self, file, l=-1, i=0):
            self._file = file
            self._l = l
            self._i = i
            super().__init__()

        def copy(self):
            return TEST_IStreamState(self._file, self._l, self._i)

        def next_line(self):
            if self.remaining():
                raise RuntimeError("!Cannot get buffer next line if not all characters in the current line have been consumed")
            self._l += 1
            self._i = 0
            return self._getl()

        def _getl(self):
            return '' if self._l == -1 else self._file.readline(self._l)

        def remaining(self):
            return len(self._getl()) - self._i

        def peek(self):
            if not self.remaining():
                raise RuntimeError("!Cannot peek buffer if all characters in the current line have been consumed")
            return self._getl()[self._i]

        def advance(self):
            if not self.remaining():
                raise RuntimeError("!Cannot advance buffer if all characters in the current line have been consumed")
            self._i += 1

        def consume_line(self):
            line = self._getl()[self._i:]
            self._i = len(self._getl())
            return line

        def consume_until(self, ends):
            i = self._i
            b = self._getl()
            while self._i < len(b) and b[self._i] not in ends: self._i += 1
            return b[i:self._i]


    class TEST_InteractiveStream:
        def __init__(self, file, *, mode=None, **settings):
            if mode is not None and not isinstance(mode, ISMode):
                raise ValueError(f"Invalid InteractiveStream mode: {mode}")

            self._mode = mode

            # global defaults
            self._settings = {**ISTREAM_DEFAULTS}

            # mode defaults
            if self._mode is not None:
                self._settings.update(ISTREAM_MODE_DEFAULTS[self._mode])

            # overwritten settings
            self._settings.update(settings)

            self._token_ends = {SPACE, EOLN}
            self._closed = False

            self._buf = TEST_IStreamState(file)
            self._read = ChainRead(self)

            super().__init__()

        def _check_open(self):
            if self._closed:
                raise RuntimeError("InteractiveStream is closed")

        def __iter__(self):
            return self

        def __next__(self):
            self._check_open()

            if self._mode == ISMode.TOKENS:
                try:
                    return self.read_token(exc=NoTokenError)
                except NoTokenError as ex:
                    raise StopIteration from ex
            else:
                try:
                    return self.read_line(exc=NoLineError)
                except NoLineError as ex:
                    raise StopIteration from ex

        def has_next(self):
            self._check_open()
            try:
                self.peek()
            except StopIteration:
                return False
            else:
                return True

        def peek(self):
            self._check_open()
            
            buf_copy = self._buf.copy()
            try:
                return next(self)
            finally:
                self._buf = buf_copy

        def __enter__(self):
            self._check_open()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self._check_open()
            self.close(exc_type=exc_type)

        def close(self, *, exc_type=None):
            if self._closed: return
            self._pending = None
            self._buf_begin = None
            self._buf_after = None

            try:
                if exc_type is None and not self._settings['extra_chars_allowed']:
                    if self._settings['ignore_blank_lines'] or self._settings['ignore_trailing_blank_lines']:
                        while True:
                            if self._buf.remaining():
                                try:
                                    self._read_eoln_or_eof(exc=NoCharError)
                                except NoCharError as ex:
                                    raise StreamError("Extra nonempty lines found at the end") from ex
                            if not self._buffer_line():
                                break
                    else:
                        if self._buf.remaining() or self._buffer_line():
                            raise StreamError("Extra characters found at the end")
            finally:
                self._closed = True

        def _buffer_line(self):
            buf = self._buf.next_line()
            if self._settings['require_trailing_eoln'] and buf and not buf.endswith(EOLN):
                raise StreamError(f"trailing {stream_char_label(EOLN)} not found")
            return buf


        def read_line(self, *, include_ends=None, ignore_trailing_spaces=None, exc=StreamError):
            self._check_open()
            self._pending = None
            self._buf_begin = None
            self._buf_after = None

            if include_ends is None:
                include_ends = self._settings['line_include_ends']
            if ignore_trailing_spaces is None:
                ignore_trailing_spaces = self._settings['line_ignore_trailing_spaces']
            if include_ends and ignore_trailing_spaces:
                raise ValueError("Cannot ignore trailing spaces if include_ends is true")

            while True:
                if not self._buf.remaining() and not self._buffer_line():
                    raise exc("no line found")

                line = self._buf.consume_line()
                assert line

                if line == EOLN and self._settings['ignore_blank_lines']:
                    continue

                # remove undesired trailing whitespace
                if not include_ends:
                    last = len(line)
                    if last and line[last - 1] == EOLN:
                        last -= 1
                    if ignore_trailing_spaces:
                        while last and line[last - 1] == SPACE:
                            last -= 1
                    line = line[:last]

                return line


        def read_token(self, *, ends=None, skip_spaces=None, skip_eolns=None, exc=StreamError):
            self._check_open()
            self._pending = None
            self._buf_begin = None
            self._buf_after = None

            if ends is None:
                ends = self._token_ends
            if skip_spaces is None:
                skip_spaces = self._settings['token_skip_spaces']
            if skip_eolns is None:
                skip_eolns = self._settings['token_skip_eolns']

            ends = force_to_set(ends)

            if not self._buf.remaining():
                self._buffer_line()

            # skip whitespace
            while self._buf.remaining() and (
                skip_spaces and self._buf.peek() == SPACE or
                skip_eolns and self._buf.peek() == EOLN):
                self._buf.advance()
                if not self._buf.remaining():
                    self._buffer_line()

            # everything skipped
            if not self._buf.remaining():
                raise exc("no token found")

            return self._buf.consume_until(ends)


        def read_spaces(self):
            self._check_open()
            self._pending = None
            self._buf_begin = None
            self._buf_after = None
            
            while self._buf.remaining() and self._buf.peek() == SPACE:
                self._buf.advance()


        def read_char(self, target, *, skip_spaces=False, exc=StreamError):
            self._check_open()
            self._pending = None
            self._buf_begin = None
            self._buf_after = None

            if skip_spaces:
                self.read_spaces()

            if isinstance(target, str):
                if len(target) > 1:
                    raise ValueError(f"Invalid argument for read_char: {target!r}")
                target = {target}
                ret = False
            else:
                target = force_to_set(target)
                ret = True

            if not self._buf.remaining():
                self._buffer_line()

            ch = self._buf.peek() if self._buf.remaining() else EOF
            if ch not in target:
                raise exc(f"{{{', '.join(map(stream_char_label, target))}}} expected but {stream_char_label(ch)} found")

            if ch != EOF:
                self._buf.advance()

            if ret:
                return ch

        def _read_eoln_or_eof(self, exc=StreamError):
            return self.read_char({EOLN, EOF}, skip_spaces=self._settings['eoln_skip_spaces'], exc=exc)

        def read_eoln(self, *, skip_spaces=None):
            if skip_spaces is None:
                skip_spaces = self._settings['eoln_skip_spaces']
            return self.read_char(EOLN, skip_spaces=skip_spaces)

        def read_eof(self, *, skip_spaces=None):
            if skip_spaces is None:
                skip_spaces = self._settings['eoln_skip_spaces']
            return self.read_char(EOF, skip_spaces=skip_spaces)

        def read_space(self):
            self.read_char(SPACE)






    def test_peeks(rand, stuff, mingood, file, mode):
        assert 0 <= mingood <= len(stuff)
        prob = rand.uniform(0.0, 0.9) if rand.random() < 0.1 else rand.uniform(0.0, 0.2)
        totake = rand.randint(mingood, len(stuff))
        with InteractiveStream(file, mode=mode) as stream:
            taken = 0
            while True:
                # print('taken', taken, totake)

                assert 0 <= taken <= totake

                if taken == totake and rand.random() < 0.1: break
                if taken == totake or rand.random() < prob:
                    # print('peeking')
                    if taken < len(stuff):
                        if rand.randrange(2):
                            res = stream.peek()
                            assert res == stuff[taken]
                        else:
                            res = stream.has_next()
                            assert res
                    else:
                        if rand.randrange(2):
                            try:
                                res = stream.peek()
                            except StopIteration:
                                res = None
                        else:
                            res = stream.has_next()
                            assert not res
                    # print('peek', repr(res))
                else:
                    # print('sunoding')
                    res = next(stream)
                    # print("sunod", repr(res))
                    assert res == stuff[taken]
                    taken += 1


    def test_incomplete(rand, stuff, mingood, file, mode, *, bad):
        assert 1 <= mingood <= len(stuff)
        prob = rand.uniform(0.0, 0.9) if rand.random() < 0.1 else rand.uniform(0.0, 0.2)
        totake = rand.randint(0, mingood - 1)
        try:
            with InteractiveStream(file, mode=mode) as stream:
                try:
                    taken = 0
                    while True:
                        # print('taken', taken, totake)

                        assert 0 <= taken <= totake

                        if taken == totake and rand.random() < 0.1: break
                        if taken == totake or rand.random() < prob:
                            # print('peeking')
                            if taken < len(stuff):
                                if rand.randrange(2):
                                    res = stream.peek()
                                    assert res == stuff[taken]
                                else:
                                    res = stream.has_next()
                                    assert res
                            else:
                                if rand.randrange(2):
                                    try:
                                        res = stream.peek()
                                    except StopIteration:
                                        res = None
                                else:
                                    res = stream.has_next()
                                    assert not res
                            # print('peek', repr(res))
                        else:
                            # print('sunoding')
                            res = next(stream)
                            # print("sunod", repr(res))
                            assert res == stuff[taken]
                            taken += 1
                except StreamError as err:
                    raise RuntimeError from err
        except StreamError as err:
            assert any(err.args == (b,) for b in bad), (err.args, bad)

    _LINES = {
            # 'eoln_skip_spaces': True,
            # 'extra_chars_allowed': False,
            'ignore_blank_lines': False,
            'ignore_trailing_blank_lines': True,
            'line_ignore_trailing_spaces': True,
            'line_include_ends': False,
            # 'parse_validate': False,
            'require_trailing_eoln': False,
            # 'token_skip_eolns': False,
            # 'token_skip_spaces': False,
        }
    def test_lines(rand, data):
        def file():
            return io.StringIO(data)

        ulines = [line.removesuffix('\n') for line in file().readlines()]
        lines = [line.rstrip(' ') for line in ulines]
        with InteractiveStream(file(), mode=ISMode.LINES) as stream:
            glines = [*stream]

        for uline, line, gline in itertools.zip_longest(ulines, lines, glines):
            ...#print('!!LIN', repr(line), repr(gline), repr(uline))

        assert len(ulines) == len(lines) == len(glines)
        assert lines == glines

        nlines = [*lines]
        while nlines and not nlines[-1]: nlines.pop()

        print()
        test_peeks(rand, lines, len(nlines), file(), ISMode.LINES)

        if nlines:
            test_incomplete(rand, lines, len(nlines), file(), ISMode.LINES, bad=[
                'Extra nonempty lines found at the end',
            ])




    _TOKENS = {
            # 'eoln_skip_spaces': True,
            # 'extra_chars_allowed': False,
            'ignore_blank_lines': True,
            'ignore_trailing_blank_lines': True,
            'line_ignore_trailing_spaces': True,
            'line_include_ends': False,
            # 'parse_validate': False,
            'require_trailing_eoln': False,
            'token_skip_eolns': True,
            'token_skip_spaces': True,
        }
    def test_tokens(rand, data):
        def file():
            return io.StringIO(data)

        stuff = 'a' + '!'*len(data) + 'b'
        tokens = [token.replace(stuff, '\t') for token in data.replace('\t', stuff).split()]
        with InteractiveStream(file(), mode=ISMode.TOKENS) as stream:
            gtokens = [*stream]

        for token, gtoken in itertools.zip_longest(tokens, gtokens):
            ...#print('!!TOK', repr(token), repr(gtoken))

        assert len(tokens) == len(gtokens)
        assert tokens == gtokens

        assert all(tokens)

        print()
        test_peeks(rand, tokens, len(tokens), file(), ISMode.TOKENS)

        if tokens:
            test_incomplete(rand, tokens, len(tokens), file(), ISMode.TOKENS, bad=[
                'Extra nonempty lines found at the end',
                # 'Extra characters found at the end',
            ])

    _RAW_LINES = {
            # 'eoln_skip_spaces': False,
            # 'extra_chars_allowed': False,
            'ignore_blank_lines': False,
            'ignore_trailing_blank_lines': False,
            'line_ignore_trailing_spaces': False,
            'line_include_ends': True,
            # 'parse_validate': False,
            'require_trailing_eoln': False,
            'token_skip_eolns': False,
            'token_skip_spaces': False,
        }
    def test_raw_lines(rand, data):
        def file():
            return io.StringIO(data)

        lines = file().readlines()
        with InteractiveStream(file(), mode=ISMode.RAW_LINES) as stream:
            glines = [*stream]

        for line, gline in itertools.zip_longest(lines, glines):
            ...#print('!!RLIN', repr(line), repr(gline))

        assert len(lines) == len(glines)
        assert lines == glines

        nlines = [*lines]
        while nlines and not nlines[-1]: nlines.pop()
        assert len(nlines) == len(lines)

        print()
        test_peeks(rand, lines, len(nlines), file(), ISMode.RAW_LINES)

        if nlines:
            test_incomplete(rand, lines, len(nlines), file(), ISMode.RAW_LINES, bad=[
                # 'Extra nonempty lines found at the end',
                'Extra characters found at the end',
            ])



    def get_result(func):
        try:
            res = func()
        except Exception as exc:
            # import traceback
            # traceback.print_exc()
            return None, exc
        else:
            return res, None




    def test_sequences(rand, data):
        mode = rand.choice([
            None,
            ISMode.LINES,
            ISMode.TOKENS,
            ISMode.RAW_LINES,
        ])
        args = [
            'extra_chars_allowed',
            'ignore_blank_lines',
            'ignore_trailing_blank_lines',
            'require_trailing_eoln',
            'parse_validate',
            'line_include_ends',
            'line_ignore_trailing_spaces',
            'token_skip_spaces',
            'token_skip_eolns',
            'eoln_skip_spaces',
        ]
        args = rand.shuff(sorted(rand.sample(args, rand.randint(0, len(args)))))
        kwargs = {arg: rand.choice([False, True]) for arg in args}
        del args

        operations = [
            lambda stream: iter(stream),
            lambda stream: next(stream),
            lambda stream: stream.has_next(),
            lambda stream: stream.peek(),
            lambda stream: stream.read_spaces(),
            lambda stream: stream.read_space(),
        ]

        dchars = [ch for ch in data if ch not in {SPACE, EOLN, EOF}] or ['a']
        def randchar():
            return rand.choice([SPACE, EOLN, EOF, rand.choice(dchars), rand.choice(dchars)])

        def make_read_line():
            # include_ends=None, ignore_trailing_spaces=None
            args = []
            kwargs = {}
            if rand.random() < 0.3:
                kwargs['include_ends'] = rand.choice([True, False, None])
            if rand.random() < 0.3:
                kwargs['ignore_trailing_spaces'] = rand.choice([True, False, None])
            return lambda stream: stream.read_line(*args, **kwargs)

        def make_read_token():
            # ends=None, skip_spaces=None, skip_eolns=None
            args = []
            kwargs = {}
            if rand.random() < 0.3:
                kwargs['ends'] = rand.choice([None,
                        rand.choice([list, set, frozenset])(randchar() for i in range(rand.randint(0, 3))),
                    ])
            if rand.random() < 0.3:
                kwargs['skip_spaces'] = rand.choice([True, False, None])
            if rand.random() < 0.3:
                kwargs['skip_eolns'] = rand.choice([True, False, None])
            return lambda stream: stream.read_line(*args, **kwargs)

        def make_read_char():
            # target, skip_spaces=False
            args = []
            kwargs = {}
            if rand.random() < 0.3:
                args.append(rand.choice([None,
                        randchar(),
                        ''.join(randchar() for i in range(rand.randint(2, 4))),
                        rand.choice([list, set, frozenset])(randchar() for i in range(rand.randint(0, 3))),
                    ]))
            if rand.random() < 0.3:
                kwargs['skip_spaces'] = rand.choice([True, False, None])
            return lambda stream: stream.read_char(*args, **kwargs)

        def make_read_eoln():
            # skip_spaces=None
            args = []
            kwargs = {}
            if rand.random() < 0.3:
                kwargs['skip_spaces'] = rand.choice([True, False, None])
            return lambda stream: stream.read_eoln(*args, **kwargs)

        def make_read_eof():
            # skip_spaces=None
            args = []
            kwargs = {}
            if rand.random() < 0.3:
                kwargs['skip_spaces'] = rand.choice([True, False, None])
            return lambda stream: stream.read_eof(*args, **kwargs)


        operationfacs = [
            make_read_line,
            make_read_token,
            make_read_char,
            make_read_eoln,
            make_read_eof,
        ]

        def produce_operations():
            for it in range(rand.randint(0, rand.choice([10, 20, 30]))):
                if rand.random() < 0.01: yield lambda stream: stream.close()
                if rand.randrange(2):
                    yield rand.choice(operations)
                else:
                    yield rand.choice(operationfacs)()

        class SimBad(Exception): pass

        def _simulate(construct, ops, aftops):
            try:
                with construct() as stream:
                    try:
                        for op in ops:
                            res, exc = get_result(lambda op=op: op(stream))
                            if res is stream: res = '[[[THIS STREAM]]]'
                            yield res, exc
                    except Exception as exc1:
                        raise SimBad from exc1
            except SimBad:
                raise
            except Exception as exc:
                yield None, exc
            else:
                yield None, None
                for op in aftops:
                    res, exc = get_result(lambda op=op: op(stream))
                    if res is stream: res = '![[[THIS STREAM]]]!'
                    yield res, exc

        def simulate(*args, append=lambda: ()):
            return ((*res, *append()) for res in _simulate(*args))

        ops = [*produce_operations()]
        aftops = [op for op in produce_operations() if rand.random() < 0.2]

        print(len(ops), len(aftops), mode, 'kwargs', kwargs)
        def file1():
            file = io.StringIO(data)
            oreadline = file.readline
            file.read_so_far = 0
            def readline():
                line = oreadline()
                file.read_so_far += 1
                assert isinstance(line, str)
                return line
            file.readline = readline
            return file

            file.readline = readline
            # shfile = lambda: 1/0
            # shfile.read_so_far = 0
            # shfile.callc = 0
            # def readline():
            #     shfile.callc += 1
            #     line = file.readline()
            #     shfile.read_so_far += 1
            #     assert isinstance(line, str)
            #     return line
            # shfile.readline = readline
            # return shfile

        def file2():
            lines = [*io.StringIO(data)]
            shfile = lambda: 1/0
            shfile.read_so_far = 0
            def readline(i):
                assert 0 <= i <= shfile.read_so_far, (i, shfile.read_so_far)
                if i == shfile.read_so_far:
                    assert 0 <= shfile.read_so_far <= len(lines)
                    if shfile.read_so_far == len(lines):
                        lines.append('')
                    assert 0 <= shfile.read_so_far < len(lines)
                    shfile.read_so_far += 1

                line = lines[i]
                assert isinstance(line, str)
                return line
            shfile.readline = readline
            return shfile

        ndrop = rand.randint(0, 30)
        IStreamState._DROP = ndrop

        file1 = file1()
        file2 = file2()
        sim1 = simulate((lambda:      InteractiveStream(file1, mode=mode, **kwargs)), ops, aftops, append=lambda: (file1.read_so_far,))
        sim2 = simulate((lambda: TEST_InteractiveStream(file2, mode=mode, **kwargs)), ops, aftops, append=lambda: (file2.read_so_far,))
        for (res1, exc1, red1), (res2, exc2, red2) in itertools.zip_longest(sim1, sim2):
            print()
            print('got')
            print(repr((res1, exc1, red1)))
            print(repr((res2, exc2, red2)))
            assert res1 == res2
            assert red1 == red2
            assert type(exc1) == type(exc2)
            assert repr(exc1) == repr(exc2)
            if exc1 is not None:
                assert exc1.args == exc2.args









    from kg.generators import KGRandom

    rand = KGRandom(11)
    rand.getrandbits(20)

    def makeprobs(n, p):
        return makeiprobs(n, rand.uniform(0, p), rand.uniform(0, p), p)

    def makeiprobs(n, l, r, p):
        if n == 0:
            return []
        if n == 1:
            return [rand.uniform(l, r)]
        if n == 2 or rand.random() < 0.5:
            return [l + (r - l) * i / (n - 1) for i in range(n)]

        m = rand.uniform(0, p)
        k = rand.randint(2, n-1)
        return makeiprobs(k, l, m, p) + makeiprobs(n+1-k, m, r, p)[1:]


    def random_data():
        # n = rand.randint(0, rand.choice([5, 11, 21, 41, 81, 121, 241]))
        n = rand.randint(0, rand.choice([5, 7, 11, 16, 21, 28, 42]))
        spacep = makeprobs(n, rand.uniform(0, 2))
        tabp = makeprobs(n, rand.uniform(0, 0.1))
        newlp = makeprobs(n, rand.uniform(0, 2))
        charp = makeprobs(n, rand.uniform(0, 2.2))
        def randch(spacep, tabp, newlp, charp):
            tl = spacep + tabp + newlp + charp
            r = rand.random() * tl
            if r < spacep: return ' '
            r -= spacep
            if r < tabp: return '\t'
            r -= tabp
            if r < newlp: return '\n'
            r -= newlp
            if r < charp: return chr(rand.randint(33, 126))
            return ' '
        res = ''.join(randch(spacep[i], tabp[i], newlp[i], charp[i]) for i in range(n))
        assert len(res) == n >= 0
        return res

    def cool_data():
        data = [v for v in random_data().replace('\n', ' ').split(' ') if v]
        edens = rand.uniform(0, 0.01) if rand.random() < 0.5 else rand.uniform(0, 0.1) if rand.random() < 0.5 else rand.uniform(0, 0.8)
        def spaces():
            while rand.random() < edens:
                yield rand.choice(' \n')
        def chs():
            yield from spaces()
            for idx, ch in enumerate(data):
                if idx > 0: yield rand.choice(' \n')
                yield ch
                yield from spaces()
        return ''.join(chs())



    z = 11111111
    for cas in range(z):
        print()
        for data in random_data(), cool_data():
            print()
            print('-'*40)
            print()
            print(f"Case {cas} of {z}: {data!r}")
            test_lines(rand, data)
            test_tokens(rand, data)
            test_raw_lines(rand, data)
            test_sequences(rand, data)
            print()
            print('-'*40)
            print()
        print()

if __name__ == '__main__':
    test_some_stuff()
### @@}
