from sys import stdout
import os.path
import pathlib
def colored(text, *a, **kw): return text
try:
    import colorama
except ImportError: 
    ...
else:
    colorama.init()
    try:
        from termcolor import colored
    except ImportError:
        ...


def attach_relpath(relpath, path):
    if not relpath or not path or path.startswith('!'):
        return path
    else:
        return os.path.join(relpath, path)

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


krazy = False
def set_krazy(k):
    global krazy
    krazy = k

_cfkeys = {
    '*': 'key',
    '@': 'err',
    '+': 'succ',
    '#': 'warn',
    '.': 'plain',
    '%': 'beginfo',
    '^': 'decor',
    '$': 'info',
}


def rand_cformat_text(x):
    import random
    return cformat_text(''.join((lambda z, y: f'[{y}[{z}]{y}]')(z, random.choice("^*#.%@+$")) for z in x))

# because termcolor.cprint sucks, I make my own...
def cprint(*args, sep=' ', end='\n', color=None, on_color=None, attrs=None, **kwargs):
    print(ctext(*args, sep=sep, end=end, color=color, on_color=on_color, attrs=attrs), end='', **kwargs)

_ultra_krazy = False
def ctext(*args, sep=' ', end='', color=None, on_color=None, attrs=None):
    global _ultra_krazy
    text = sep.join(map(str, args)) + end
    if krazy and not _ultra_krazy:
        _ultra_krazy = True
        try:
            return rand_cformat_text(text)
        finally:
            _ultra_krazy = False
    else:
        return colored(text, color=color, on_color=on_color, attrs=attrs)

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

PLAIN = None
def plain_print(*a, **kw): cprint(*a, **kw)
def plain_text(*a, **kw): return ctext(*a, **kw)

def cformat_text(s, begin='info'):
    envs = []
    parts = []
    def push(t):
        if envs:
            st, u = envs[-1]
            parts.append((st, ''.join(u)))
            envs[-1][1][:] = []
        envs.append((t, []))
    def pop(t):
        st, u = envs.pop()
        if t != st: raise ValueError("Invalid cformat_text: mismatch")
        parts.append((st, ''.join(u)))

    push(begin)

    prev = ['', '']
    for curr in s:
        prev.append(curr)
        if prev[0] == prev[2] == '[' and prev[1] in _cfkeys:
            envs[-1][1].pop(); envs[-1][1].pop()
            push(_cfkeys[prev[1]])
        elif prev[0] == prev[2] == ']' and prev[1] in _cfkeys:
            envs[-1][1].pop(); envs[-1][1].pop()
            pop(_cfkeys[prev[1]])
        else:
            envs[-1][1].append(curr)
        prev = prev[1:]

    pop(begin)
    if envs: raise ValueError("Invalid cformat_text: unclosed")
    return ''.join(globals()[part + '_text'](s) for part, s in parts)
