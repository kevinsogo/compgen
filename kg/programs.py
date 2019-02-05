import os.path
import subprocess
from collections import defaultdict
import json

script_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(script_path, 'data', 'langs.json')) as f:
    langs = json.load(f)

lang_of_ending = {ending: lang for lang, data in langs.items() for ending in data['endings']}
def infer_lang(filename):
    base, ext = os.path.splitext(filename)
    return lang_of_ending.get(ext)

class Program:
    def __init__(self, filename, compile_, run):
        if not filename: raise ValueError("Filename cannot be empty")
        self.filename = filename
        self.compile = compile_
        self.run = run
        self._compiled = False
        super(Program, self).__init__()

    def do_compile(self):
        if self.compile: subprocess.run(self.compile, check=True)
        self._compiled = True

    def do_run(self, *args, input=None, stdin=None, stdout=None, stderr=None, time=False, check=True):
        if not self._compiled: raise Exception("Compile the program first")
        command = self.run + list(args)
        if time: command = ['/usr/bin/time', '-f' 'TIME %es %Us %Ss'] + command
        kwargs = dict(input=input, stdin=stdin, stdout=stdout, stderr=stderr, check=check)
        if not input: kwargs.pop('input')
        if not stdin: kwargs.pop('stdin')
        return subprocess.run(command, **kwargs)

    def matches_abbr(self, abbr):
        return os.path.splitext(os.path.basename(self.filename))[0] == abbr

    def __str__(self):
        return "<{}\n    {}\n    {}\n    {}\n>".format(self.__class__.__name__, self.filename, self.compile, self.run)

    def __repr__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__, repr(self.filename), repr(self.compile), repr(self.run))


    @classmethod
    def from_data(cls, arg):
        if isinstance(arg, list):
            if len(arg) == 2:
                filename, run = arg
                compile_ = ''
            elif len(arg) == 3:
                filename, compile_, run = arg
            else:
                raise Exception("Cannot understand program data: {}".format(str(arg)))
        elif isinstance(arg, str):
            lang = infer_lang(arg)
            if not lang:
                raise Exception("Cannot infer language: {}".format(str(arg)))
            filename = arg
            env = {
                'filename': filename,
                'filename_base': os.path.splitext(os.path.basename(filename))[0],
            }
            compile_ = env['compile'] = langs[lang]['compile'].format(**env)
            run = langs[lang]['run'].format(**env)
        else:
            raise Exception("Unknown program type: {}".format(repr(arg)))

        return cls(filename, compile_.split(), run.split())

    @classmethod
    def from_args(cls, file, command):
        if command:
            return cls(file or '!custom', [], command)
        elif file:
            return cls.from_data(file)

    @classmethod
    def noop(cls):
        return cls('!noop', [], ['kg-noop'])

