from sys import stdout
import os.path
import pathlib
def colored(text, *a, **kw): return text
try:
    import colorama
except ImportError: 
    ...
else:
    try:
        from termcolor import colored
    except ImportError:
        ...
    else:
        colorama.init()



def set_handler(parser, default_file=stdout):
    def _set_handler(handler):
        parser.set_defaults(handler=handler, default_file=default_file)
        # return handler # Let's not return this, to ensure that they are not called.
    return _set_handler


def touch_container(file):
    ''' ensures that the folder containing "file" exists, possibly creating the nested directory path to it '''
    touch_dir(os.path.dirname(file))


def touch_dir(dirname):
    if not os.path.exists(dirname): info_print('Creating folder:', dirname)
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)


# because termcolor.cprint sucks, I make my own...
def cprint(*args, sep=' ', end='\n', color=None, on_color=None, attrs=None, **kwargs):
    print(ctext(*args, sep=sep, end=end, color=color, on_color=on_color, attrs=attrs), end='', **kwargs)

def ctext(*args, sep=' ', end='', color=None, on_color=None, attrs=None):
    return colored(sep.join(map(str, args)) + end, color=color, on_color=on_color, attrs=attrs)

SUCC = 'green'
def succ_print(*a, **kw): cprint(*a, color=SUCC, **kw)
def succ_text(*a, **kw): return ctext(*a, color=SUCC, **kw)

BEGINFO = 'cyan'
def beginfo_print(*a, **kw): cprint(*a, color=BEGINFO, **kw)
def beginfo_text(*a, **kw): return ctext(*a, color=BEGINFO, **kw)

INFO = 'blue'
def info_print(*a, **kw): cprint(*a, color=INFO, **kw)
def info_text(*a, **kw): return ctext(*a, color=INFO, **kw)

WARN = 'yellow'
def warn_print(*a, **kw): cprint(*a, color=WARN, **kw)
def warn_text(*a, **kw): return ctext(*a, color=WARN, **kw)

ERR = 'red'
def err_print(*a, **kw): cprint(*a, color=ERR, **kw)
def err_text(*a, **kw): return ctext(*a, color=ERR, **kw)

DECOR = 'cyan'
def decor_print(*a, **kw): cprint(*a, color=DECOR, **kw)
def decor_text(*a, **kw): return ctext(*a, color=DECOR, **kw)

KEY = 'green'
def key_print(*a, **kw): cprint(*a, color=KEY, **kw)
def key_text(*a, **kw): return ctext(*a, color=KEY, **kw)

