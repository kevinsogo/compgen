from functools import wraps

def ensure(condition, message=None):
    ''' assert that doesn't raise AssertionError. Useful/Convenient for judging. '''
    if not condition:
        try:
            message = message()
        except TypeError:
            pass
        if isinstance(message, str):
            message = Exception(message)
        raise message or Exception()


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


