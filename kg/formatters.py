import functools

from .utils import * ### @import
from .utils.streams import * ### @import

def formatter(f=None, *, print=print):
    def _d(f):
        @functools.wraps(f)
        def _f(file, case, *args, **kwargs):
            with InteractiveStream(None, file) as stream:
                # add a print function reploaded with this file
                kwargs.setdefault('print', stream.print)
                return f(stream, case, *args, **kwargs)
        return _f
    return _d(f) if f is not None else _d
