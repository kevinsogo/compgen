from collections import defaultdict
from sys import stderr
import json
import os
import os.path
import subprocess
import time as timel

from .utils import *

class ExtProgramError(Exception): ...

with open(os.path.join(kg_data_path, 'langs.json')) as f:
    langs = json.load(f)

lang_of_ending = {ending: lang for lang, data in langs.items() for ending in data['endings']}
def infer_lang(filename):
    base, ext = os.path.splitext(filename)
    return lang_of_ending.get(ext)

@listify
def _strip_prefixes(command, *prefixes):
    for part in command:
        for pref in prefixes:
            if part.startswith(pref):
                yield part[len(pref):]
                break
        else:
            yield part

def _get_python3_command(*, verbose=True):
    """
    Get the first python3 command that has 'kg' installed, among "pypy3", "python3", "python", and "py".
    "kg" is detected as being installed if 'from kg import main' succeeds.
    """
    if verbose: info_print("getting python3 command...", end='', file=stderr, flush=True)
    previous = []
    for command in ['pypy3', 'python3', 'python', 'py']:
        try:
            subprocess.run([command, '-c', 'from kg import main'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True)
        except Exception:
            previous.append(command)
        else:
            if verbose: print(info_text("got"), key_text(command),
                              info_text(f"('kg' not found in {', '.join(previous)})" if previous else ''),
                              file=stderr)
            return command
    fallback = 'python3'
    if verbose: print(warn_text("\nWarning: falling back to"), key_text(fallback),
                      warn_text(f"even if 'import kg' failed! ('kg' not found in {', '.join(previous)})"),
                      file=stderr)
    return fallback

python3_command = None
def get_python3_command(*, verbose=True):
    global python3_command
    if not python3_command: python3_command = _get_python3_command(verbose=verbose)
    return python3_command

class Program:
    def __init__(self, filename, compile_, run, *, relpath=None, strip_prefixes=['___'], check_exists=True):
        if not filename: raise ValueError("Filename cannot be empty")
        if not run: raise ValueError("A program cannot have an empty run command")
        self.relpath = relpath
        self.filename = filename
        self.rel_filename = attach_relpath(relpath, filename)
        if check_exists and not self.rel_filename.startswith('!') and not os.path.exists(self.rel_filename):
            raise ValueError(f"File {self.rel_filename} not found.")

        env = {
            'loc': relpath,
            'sep': os.sep,
            'filename': filename,
            'rel_filename': self.rel_filename,
            'python3': get_python3_command(),
            'filename_base': os.path.splitext(os.path.basename(filename))[0],
        }
        self.compile = env['compile'] = _strip_prefixes([p.format(**env) for p in compile_], *strip_prefixes)
        self.run = _strip_prefixes([p.format(**env) for p in run], *strip_prefixes)
        self.compiled = False
        super().__init__()

    def do_compile(self, *, force=False, **kwargs):
        if (force or not self.compiled) and self.compile:
            info_print(f"Compiling {self.filename}", file=stderr)
            kwargs.setdefault('cwd', self.relpath)
            kwargs.setdefault('check', True)
            subprocess.run(self.compile, **kwargs)
        self.compiled = True
        return self

    def do_run(self, *args, time=False, **kwargs):
        if not self.compiled: raise ExtProgramError("Compile the program first")
        command = self.run + list(args)
        kwargs.setdefault('cwd', self.relpath)
        kwargs.setdefault('check', True)
        if time:
            start_time = timel.time()
            if os.name != 'nt':
                command = ['/usr/bin/time', '-f' 'ELAPSED TIME from /usr/bin/time %esec %Usec %Ssec'] + command
        try:
            return subprocess.run(command, **kwargs)
        except Exception:
            raise
        finally:
            if time:
                self.last_running_time = elapsed = timel.time() - start_time
                info_print(f"ELAPSED TIME from time.time(): {elapsed:.2f}sec", file=stderr)

    def matches_abbr(self, abbr):
        return os.path.splitext(os.path.basename(self.filename))[0] == abbr

    def __str__(self):
        return (f"<{self.__class__.__name__}\n"
                f"    {self.filename}\n"
                f"    {self.compile}\n"
                f"    {self.run}\n"
                f"    at relpath {self.relpath}\n"
                 ">")

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"{repr(self.filename)}, "
                f"{repr(self.compile)}, "
                f"{repr(self.run)}, "
                f"relpath={self.relpath})")


    @classmethod
    def from_data(cls, arg, *, relpath=None):
        if isinstance(arg, list):
            if len(arg) == 2:
                filename, run = arg
                compile_ = ''
            elif len(arg) == 3:
                filename, compile_, run = arg
            else:
                raise ExtProgramError(f"Cannot understand program data: {repr(arg)}")
        elif isinstance(arg, str):
            lang = infer_lang(arg)
            if not lang:
                raise ExtProgramError(f"Cannot infer language: {repr(arg)}")
            filename = arg
            compile_ = langs[lang]['compile']
            run = langs[lang]['run']
        else:
            raise ExtProgramError(f"Unknown program type: {repr(arg)}")

        return cls(filename, compile_.split(), run.split(), relpath=relpath)

    @classmethod
    def from_args(cls, file, command, *, relpath=None):
        if command:
            return cls(file or '!custom', [], command, relpath=relpath)
        elif file:
            return cls.from_data(file, relpath=relpath)

    @classmethod
    def noop(cls):
        return cls('!noop', [], ['kg-aux', 'noop'])

