import os.path
import subprocess
from subprocess import Popen, PIPE
from collections import defaultdict

langs = {
    'py': {
        'compile': '',
        'run': 'python {filename}',
        'endings': ['.py'],
    },
    'py2': {
        'compile': '',
        'run': 'python2 {filename}',
        'endings': ['.py2'],
    },
    'py3': {
        'compile': '',
        'run': 'python3 {filename}',
        'endings': ['.py3'],
    },
    'java': {
        'compile': 'javac {filename}',
        'run': 'java {filename_base}',
        'endings': ['.java'],
    },
    'cpp': {
        'compile': 'g++ -O2 -std=c++17 {filename} -o {filename}.executable',
        'run': './{filename}.executable',
        'endings': ['.c', '.cpp', '.c++'],
    },
}
lang_of_ending = {ending: lang for lang, data in langs.items() for ending in data['endings']}
def infer_lang(filename):
    base, ext = os.path.splitext(filename)
    if ext in lang_of_ending:
        return lang_of_ending[ext]

class Program:
    def __init__(self, filename, compile_, run):
        self.filename = filename
        self.compile = compile_
        self.run = run
        self._compiled = False
        super(Program, self).__init__()

    def do_compile(self):
        if self.compile:
            subprocess.call(self.compile)
        self._compiled = True

    def _compile_first(self):
        if not self._compiled:
            self.do_compile()

    def do_run(self, *args, inp=None):
        self._compile_first()
        if inp:
            with open(inp) as f:
                return Popen(self.run + list(args), stdin=f, stdout=PIPE, stderr=PIPE).communicate()
        else:
            return Popen(self.run + list(args), stdout=PIPE, stderr=PIPE).communicate()

    def __str__(self):
        return "<Program\n{}\n{}\n{}\n>".format(self.filename, self.compile, self.run)

    def __repr__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__, repr(self.filename), repr(self.compile), repr(self.run))


    @classmethod
    def from_data(cls, arg):
        if isinstance(arg, list):
            if len(arg) == 2:
                filename, run = arg
                compile_ = ''
            if len(arg) == 3:
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
            return cls(file or '', '', command)
        elif file:
            return cls.from_data(file)
