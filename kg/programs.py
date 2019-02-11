from collections import defaultdict
import json
import os
import os.path
import subprocess
from sys import stderr
import time as timel

from .iutils import *

class ExtProgramError(Exception): ...

script_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(script_path, 'data', 'langs.json')) as f:
    langs = json.load(f)

lang_of_ending = {ending: lang for lang, data in langs.items() for ending in data['endings']}
def infer_lang(filename):
    base, ext = os.path.splitext(filename)
    return lang_of_ending.get(ext)

def attach_relpath(relpath, path):
    if not relpath or not path or path.startswith('!') or os.path.isabs(path):
        return path
    else:
        return os.path.join(relpath, path)

class Program:
    def __init__(self, filename, compile_, run, *, relpath=None):
        if not filename: raise ValueError("Filename cannot be empty")
        self.filename = attach_relpath(relpath, filename)
        env = {
            'loc': relpath,
            'sep': os.sep,
            'filename': self.filename,
            'raw_filename': filename,
            'filename_base': os.path.splitext(os.path.basename(filename))[0],
        }
        self.compile = env['compile'] = [p.format(**env) for p in compile_]
        self.run = [p.format(**env) for p in run]
        self._compiled = False
        super(Program, self).__init__()

    def do_compile(self):
        if self.compile: subprocess.run(self.compile, check=True)
        self._compiled = True

    def do_run(self, *args, input=None, stdin=None, stdout=None, stderr=None, time=False, check=True):
        if not self._compiled: raise ExtProgramError("Compile the program first")
        command = self.run + list(args)
        kwargs = dict(input=input, stdin=stdin, stdout=stdout, stderr=stderr, check=check)
        if not input: kwargs.pop('input')
        if not stdin: kwargs.pop('stdin')
        if time:
            start_time = timel.time()
            if os.name != 'nt': command = ['/usr/bin/time', '-f' 'ELAPSED TIME %esec %Usec %Ssec'] + command
        try:
            return subprocess.run(command, **kwargs)
        except Exception:
            raise
        finally:
            if time:
                elapsed = timel.time() - start_time
                info_print(f"ELAPSED TIME from time.time(): {elapsed:.2f}sec", file=stderr)

    def matches_abbr(self, abbr):
        return os.path.splitext(os.path.basename(self.filename))[0] == abbr

    def __str__(self):
        return f"<{self.__class__.__name__}\n    {self.filename}\n    {self.compile}\n    {self.run}\n>"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.filename)}, {repr(self.compile)}, {repr(self.run)})"


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
        return cls('!noop', [], ['kg-noop'])

