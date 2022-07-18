from collections import defaultdict
from functools import wraps
from sys import stderr
from threading import Thread
import json
import os
import os.path
import subprocess
import time as timel

from .utils import *

class ProgramsError(Exception): ...

class InteractorException(ProgramsError):
    def __init__(self, original_error, *args, **kwargs):
        self.original_error = original_error
        super().__init__(f"Original error: {original_error}", *args, **kwargs)

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

def _get_python3_command(*, fallback='python3', lowest_version=8, highest_version=10, verbose=True):
    """Get the first python3 command that has KompGen installed.

    We prioritize the commends in the following order:

        - pypy3.*, python3.* (higher versions first)
        - pypy3
        - python3
        - py3
        - python
        - py

    KompGen is detected as being installed if 'from kg import main' succeeds.

    'import kg' may not be enough because after uninstalling, the import may still succeed,
    though 'kg' will just be an empty module.
    """
    if verbose: info_print("getting python3 command...", end='', file=stderr, flush=True)
    previous = set()
    def commands():
        for v in range(highest_version, lowest_version-1, -1):
            for py in 'pypy3', 'python3':
                yield f'{py}.{v}'
        yield 'pypy3'
        yield 'python3'
        yield 'py3'
        yield 'python'
        yield 'py'
        yield fallback
    for command in commands():
        try:
            subprocess.run([command, '-c', 'from kg import main'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True)
        except Exception:
            previous.add(command)
        else:
            if verbose: print(info_text("got"), key_text(command),
                              info_text(f"('kg' not found in {', '.join(previous)})" if previous else ''),
                              file=stderr)
            return command
    if verbose:
        print(
            warn_text("\nWarning: falling back to"), key_text(fallback),
            warn_text(f"even if kg wasn't found there! ('kg' not found in {', '.join(previous)})"),
            file=stderr)
    return fallback

python3_command = None
def get_python3_command(*, verbose=True):
    global python3_command
    if not python3_command: python3_command = _get_python3_command(verbose=verbose)
    return python3_command


def _fix_timeout(kwargs):
    # be careful with timeout when the program creates subprocesses... the children processes are not killed,
    # so multiple slow (and potentially memory-consuming) programs could be running in the background!!
    kwargs.setdefault('timeout', float('inf'))

    # cap the timeout to min(TL*3, TL+10) so it doesn't run that slowly
    if 'time_limit' in kwargs:
        kwargs['timeout'] = min(kwargs['timeout'], max(0.1, kwargs['time_limit'] * 3), kwargs['time_limit'] + 10)
        del kwargs['time_limit']

    if kwargs['timeout'] >= float('inf'):
        del kwargs['timeout']
    else:
        info_print(f"  force timeout after {kwargs['timeout']:.2f} sec.", file=stderr)

class Program:
    def __init__(self, filename, compile_, run, *, relpath=None, strip_prefixes=['___'], check_exists=True, **attributes):
        if not filename: raise ValueError("Filename cannot be empty")
        if not run: raise ValueError("A program cannot have an empty run command")
        self.relpath = relpath
        self.filename = filename
        self.rel_filename = attach_relpath(relpath, filename)
        self.attributes = attributes
        if check_exists and not self.rel_filename.startswith('!') and not os.path.exists(self.rel_filename):
            raise ValueError(f"File {self.rel_filename} not found.")

        env = {
            'loc': relpath,
            'sep': os.sep,
            'filename': filename,
            'rel_filename': self.rel_filename,
            'python3': get_python3_command(),
            'filename_path': os.path.dirname(self.rel_filename),
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
            self._run(self.compile, **kwargs)
        self.compiled = True
        return self

    def get_runner_process(self, *args, **kwargs):
        if not self.compiled: raise ProgramsError("Compile the program first")
        command = self.run + list(args)
        kwargs.setdefault('cwd', self.relpath)
        return subprocess.Popen(command, **kwargs)

    def do_run(self, *args, time=False, label=None, **kwargs):
        if not self.compiled: raise ProgramsError("Compile the program first")
        command = self.run + list(args)
        kwargs.setdefault('cwd', self.relpath)
        kwargs.setdefault('check', True)
        _fix_timeout(kwargs)
        if time:
            start_time = timel.time()
        try:
            return self._run(command, **kwargs)
        finally:
            if time:
                self.last_running_time = elapsed = timel.time() - start_time
                info_print(f'{label or "":>18} elapsed time: {elapsed:.2f} sec.', file=stderr)

    def _run(self, *args, **kwargs):
        try:
            return subprocess.run(*args, **kwargs)
        except Exception as exc:
            err_print("An exception was raised while running", *args, "with", kwargs, file=stderr)
            err_print("The exception is:", file=stderr)
            err_print(f'    {exc!r}', file=stderr)
            err_print(f'    {exc}', file=stderr)
            err_print("The current program is:", self, file=stderr)
            raise

    def _do_run_process(self, process, *, time=False, label=None, check=False, timeout=None):
        if time:
            start_time = timel.time()
        with process as proc:  # just to be safe; maybe in the future, Popen.__enter__ might return something else
            try:
                retcode = proc.wait(timeout=timeout)
            except:
                proc.kill()
                raise
            finally:
                if time:
                    self.last_running_time = elapsed = timel.time() - start_time
                    info_print(f'{label or "":>18} elapsed time: {elapsed:.2f} sec.', file=stderr)
            retcode = proc.poll()

            if check and retcode:
                raise subprocess.CalledProcessError(retcode, proc.args, output=None, stderr=None)

        return subprocess.CompletedProcess(proc.args, None, None, retcode)


    def do_interact(self, interactor, *args, time=False, label=None, check=False,
                    interactor_args=(), interactor_kwargs=None,  **kwargs):
        """Interact with 'interactor' by connecting their stdins and stdouts together."""
        if not interactor:
            raise ProgramsError("No interactor passed")
        for stream in 'stdin', 'stdout':
            if stream in kwargs or stream in interactor_kwargs:
                raise ProgramsError(f"You cannot pass {stream!r} to interactors")

        _fix_timeout(kwargs)

        # we can't pass timeout to the process constructor, so we take it, and then
        # pass it to when we run it.
        timeout = kwargs.pop('timeout', None)

        process = self.get_runner_process(*args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, **kwargs)

        # connect them
        if not interactor_kwargs: interactor_kwargs = {}
        interactor_kwargs.setdefault('label', 'INTERACTOR')
        interactor_kwargs['stdin'] = process.stdout
        interactor_kwargs['stdout'] = process.stdin

        # start the interaction
        def interactor_run(*args, **kwargs):
            # TODO find a better way than monkeying around like this
            interactor_run.thrown = None
            interactor_run.result = None
            try:
                result = interactor.do_run(*args, **kwargs)
            except Exception as thrown:
                interactor_run.thrown = thrown
            else:
                interactor_run.result = result
                return result

            return new_target

        interactor_thread = Thread(target=interactor_run, args=interactor_args, kwargs=interactor_kwargs)
        interactor_thread.start()
        result = self._do_run_process(process, time=time, label=label, check=check, timeout=timeout)
        interactor_thread.join()

        # too much monkeying around!! help. also, think about thread safety...
        if interactor_run.thrown: raise InteractorException(interactor_run.thrown)
        return result, interactor_run.result


    def do_interact_nodes(self, n, node, *args, pass_id=True, time=False, label=None, check=False,
                          node_args=(), node_kwargs=None, **kwargs):
        """Interact with 'n' copies of 'node'.
        
        The nodes will be indexed 0 to n-1. If 'pass_id' is True, the ID will be passed to each node as an arg.

        This will create n FIFO pairs, one for each node.

        The FIFO names will be passed as args: --from-user [...] --to-user [...]
        """
        if not node:
            raise ProgramsError("No node passed")
        for stream in 'stdin', 'stdout':
            if stream in kwargs or stream in interactor_kwargs:
                raise ProgramsError(f"You cannot pass {stream!r} to interactors")
        # TODO


    def matches_abbr(self, abbr):
        return os.path.splitext(os.path.basename(self.filename))[0] == abbr

    def __str__(self):
        return (f"<{self.__class__.__name__}\n"
                f"    {self.filename}\n"
                f"    {self.compile}\n"
                f"    {self.run}\n"
                f"    at relpath {self.relpath}\n"
                 ">")

    __repr__ = __str__


    @classmethod
    def from_data(cls, arg, *, relpath=None):
        attributes = arg.pop() if arg and isinstance(arg, list) and isinstance(arg[-1], dict) else {} 

        if isinstance(arg, str): arg = [arg]
        if isinstance(arg, list):
            if len(arg) == 1:
                filename, = arg
                lang = infer_lang(filename)
                if not lang: raise ProgramsError(f"Cannot infer language: {filename!r}")
                compile_ = langs[lang]['compile']
                run = langs[lang]['run']
            elif len(arg) == 2:
                filename, run = arg
                compile_ = ''
            elif len(arg) == 3:
                filename, compile_, run = arg
            else:
                raise ProgramsError(f"Cannot understand program data: {arg!r}")
        else:
            raise ProgramsError(f"Unknown program type: {arg!r}")

        return cls(filename, compile_.split(), run.split(), relpath=relpath, **attributes)

    @classmethod
    def from_args(cls, file, command, *, relpath=None):
        if command:
            return cls(file or '!custom', [], command, relpath=relpath)
        elif file:
            return cls.from_data(file, relpath=relpath)

    @classmethod
    def noop(cls):
        return cls('!noop', [], ['kg-aux', 'noop'])

