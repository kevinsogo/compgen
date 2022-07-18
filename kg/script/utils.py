from sys import stdout, stderr
import calendar
import concurrent.futures
import os
import os.path
import pathlib
import shutil
import stat

from jinja2 import Environment, select_autoescape, FileSystemLoader

from ..utils import *
from ..utils.hr import *

script_path = os.path.dirname(os.path.realpath(__file__))
kg_path = os.path.normpath(os.path.join(script_path, '..'))
kg_data_path = os.path.normpath(os.path.join(kg_path, 'data'))
kg_contest_template = os.path.join(kg_data_path, 'contest_template')
kg_problem_template = os.path.join(kg_data_path, 'template')


# aux functions

def touch_container(file):
    ''' ensures that the folder containing "file" exists, possibly creating the nested directory path to it '''
    touch_dir(os.path.dirname(file))


def touch_dir(dirname):
    if not os.path.exists(dirname): info_print('Creating folder:', dirname)
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)


def copy_file(source, dest, ensure_container=True):
    if ensure_container: touch_container(dest)
    shutil.copyfile(source, dest)

def make_executable(filename):
    os.chmod(filename, os.stat(filename).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)



# Jinja stuff

kg_template_env = Environment(loader=FileSystemLoader(kg_data_path),
                              trim_blocks=True,
                              lstrip_blocks=True,
                              autoescape=select_autoescape(
                                enabled_extensions=('html.j2', 'xml.j2'),
                                default_for_string=True))

def set_template_filter(filter_name):
    def _set_template_filter(f):
        if filter_name in kg_template_env.filters: raise
        kg_template_env.filters[filter_name] = f
        return f
    return _set_template_filter


@set_template_filter('basename')
def basename_filter(file):
    return os.path.basename(file)


@set_template_filter('hms')
def hms_filter(dt):
    seconds = int(dt.total_seconds())
    return f"{seconds // 3600}:{seconds // 60 % 60 :02}:{seconds % 60 :02}"

@set_template_filter('timestamp')
def timestamp_filter(dt):
    return calendar.timegm(dt.utctimetuple())

@set_template_filter('with_letter')
def with_letter_filter(title, letter=None):
    return f"{letter}: {title}"


def kg_render_template(template_filename, **env):
    template_name = '/'.join(os.path.split(os.path.relpath(template_filename, kg_data_path)))
    return kg_template_env.get_template(template_name).render(**env)


def kg_render_template_to(template_filename, dest_filename, **env):
    touch_container(dest_filename)
    with open(dest_filename, 'w') as dest_file:
        dest_file.write(kg_render_template(template_filename, **env))


# Color stuff

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
    return cformat_text(''.join('[{y}[{z}]{y}]'.format(z=z, y=random.choice("^*#.%@+$")) for z in x))

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

SRC = 'cyan'
def src_print(*a, **kw): cprint(*a, color=SRC, **kw)
def src_text(*a, **kw): return ctext(*a, color=SRC, **kw)

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



def wait_all(futures, info=None, executor=None, logf=stderr):
    info = f"Task [{info}]" if info else "Task"
    info_print(info, f"waiting", file=logf)
    futures = [*futures]
    dones, not_dones = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_EXCEPTION)
    for done in dones:
        try:
            done.result()
        except Exception as exc:
            info_print(info, f"failed with error", file=logf)
            info_print(f"    {exc!r}", file=logf)
            info_print(f"    {exc}", file=logf)
            info_print(info, f"cancelling", file=logf)
            if executor: executor.shutdown(cancel_futures=True)
            for future in futures: future.cancel()
            info_print(info, f"cancelled", file=logf)
            raise

    assert not not_dones
    
    info_print(info, f"finished", file=logf)
    return [done.result() for done in dones]


def thread_pool_executor(task, *, max_workers, thread_name_prefix, logf=stderr, **kwargs):
    info_print(
            task,
            f"with {max_workers or 'several'} worker threads ({os.cpu_count()} CPUs)... "
            f"thread prefix is {thread_name_prefix!r}",
            file=stderr)
    if kwargs: info_print("Other args are", kwargs, file=stderr)
    return concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            **kwargs)
