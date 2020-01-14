import functools
def formatter(print=print):
    def _formatter(f):
        @functools.wraps(f)
        def new_f(file, case, *args, **kwargs):
            # add a custom print function
            if 'print' not in kwargs:
                kwargs['print'] = functools.partial(print, file=file)
            return f(file, case, *args, **kwargs)
        return new_f
    return _formatter
