from collections import defaultdict, namedtuple
from contextlib import contextmanager, ExitStack
from enum import Enum
from functools import wraps, partial
from itertools import chain
from sys import stderr
from threading import Thread
import json
import os
import os.path
import stat
import subprocess
import tempfile
import time as timel

from .utils import *

class IMode(Enum):
    STDIO = 'stdio'
    FIFO = 'fifo'

class ProgramsError(Exception): ...

ProgramResult = namedtuple('ProgramResult', ['result', 'running_time'])

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
            self._run(True, subprocess.run, self.compile, **kwargs)
        self.compiled = True
        return self

    def get_runner_process(self, *args, **kwargs):
        if not self.compiled: raise ProgramsError("Compile the program first")
        command = [*self.run, *args]
        kwargs.setdefault('cwd', self.relpath)
        return subprocess.Popen(command, **kwargs)

    def do_run(self, *args, time=False, label=None, log_exc=True, **kwargs):
        if not self.compiled: raise ProgramsError("Compile the program first")
        command = [*self.run, *args]
        kwargs.setdefault('cwd', self.relpath)
        kwargs.setdefault('check', True)
        _fix_timeout(kwargs)
        if 'timeout' in kwargs:
            info_print(f"  will force timeout after {kwargs['timeout']:.2f} sec.", file=stderr)
        if time:
            start_time = timel.time()
        try:
            res = self._run(log_exc, subprocess.run, command, **kwargs)
        finally:
            if time:
                elapsed = timel.time() - start_time
                info_print(f'{label or "":>18} elapsed time: {elapsed:.2f} sec.', file=stderr)
            else:
                elapsed = None

        return ProgramResult(result=res, running_time=elapsed)

    def _run(self, log_exc, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if log_exc:
                err_print("The ff exception was raised:", file=stderr)
                err_print(f'    {exc!r}', file=stderr)
                err_print(f'    {exc}', file=stderr)
                err_print("while running", func, file=stderr)
                err_print("      args", args, file=stderr)
                err_print("    kwargs", kwargs, file=stderr)
                err_print("The current program is:", self, file=stderr)
            raise

    def _do_run_process(self, process, *, time=False, label=None, check=False, log_exc=True, timeout=None):
        if time:
            start_time = timel.time()
        with process as proc:  # just to be safe; maybe in the future, Popen.__enter__ might return something else
            try:
                retcode = self._run(log_exc, proc.wait, timeout=timeout)
            except Exception as exc:
                proc.kill()
                raise
            finally:
                if time:
                    elapsed = timel.time() - start_time
                    info_print(f'{label or "":>18} elapsed time: {elapsed:.2f} sec.', file=stderr)
                else:
                    elapsed = None
            retcode = proc.poll()

            if check and retcode:
                raise subprocess.CalledProcessError(retcode, proc.args, output=None, stderr=None)

        return ProgramResult(result=subprocess.CompletedProcess(proc.args, None, None, retcode), running_time=elapsed)


    def do_interact(self, interactor, *args, time=False, label=None, check=False, log_exc=True,
                    node_count=1, interaction_mode=IMode.STDIO, pass_id=False,
                    interactor_args=(), interactor_kwargs=None, **kwargs):
        """Interact with 'interactor'.

        There will be 'node_count' copies of the current program, and one copy of the interactor.
        The default node_count is 1.

        The nodes will be indexed 0 to node_count-1. If 'pass_id' is True, the ID will be passed to each node as an arg.
        The default pass_id is False.

        The mode of interaction depends on 'interaction_mode':

        In STDIO mode (default):
        - Their stdins and stdouts are woven together. Note that node_count must be 1 in this mode.

        In FIFO mode:
        - The communication will be done via FIFOs.
        - A FIFO pair will be created for each node, for a total of 2*node_count FIFOs.
        - The FIFO names will be passed to the interactor as args: --from-user [...] --to-user [...]
        - This probably isn't possible in windows because there are no FIFOs there.
        """
        if not interactor:
            raise ProgramsError("No interactor passed")

        for stream in 'stdin', 'stdout':
            if stream in kwargs:
                raise ProgramsError(f"You cannot pass the {stream!r} argument to the node if there's an interactor")

        if node_count is None: node_count = 1
        if node_count < 1:
            raise ProgramsError(f"node_count must be at least 1; got {node_count}")

        interaction_mode = IMode(interaction_mode)
        if node_count > 1 and interaction_mode != IMode.FIFO:
            raise ProgramsError("The interaction mode must be 'fifo' if there is more than one node")

        _fix_timeout(kwargs)
        if 'timeout' in kwargs:
            info_print(f"  will force timeout after {kwargs['timeout']:.2f} sec.", file=stderr)

        # we can't pass 'timeout' to the process constructor, so we take it, and then pass it to when we run it.
        timeout = kwargs.pop('timeout', None)

        # setup the interactor args and kwargs
        interactor_args = [*(interactor_args or ())]
        interactor_kwargs = {**(interactor_kwargs or {})}
        interactor_kwargs.setdefault('label', 'INTERACTOR')

        # set a slightly larger timeout for the interactor
        interactor_kwargs.setdefault('timeout', float('inf'))
        ext_timeout = None
        if timeout is not None:
            ext_timeout = timeout + 2
            interactor_kwargs['timeout'] = min(interactor_kwargs['timeout'], ext_timeout)
        if interactor_kwargs['timeout'] >= float('inf'):
            del interactor_kwargs['timeout']
        else:
            info_print(f"  the timeout for the interactor is {interactor_kwargs['timeout']:.2f} sec.", file=stderr)

        @contextmanager
        def prepare_communication():
            # setup communication channels
            pargses = [[*args, *([str(idx)] if pass_id else [])] for idx in range(node_count)]

            # TODO match statement
            if interaction_mode == IMode.STDIO:

                info_print("Weaving the stdin and stdout of the node and the interactor")
                for stream in 'stdin', 'stdout':
                    if stream in interactor_kwargs:
                        raise ProgramsError(f"You cannot pass the {stream!r} argument to the interactor in 'stdio' mode")
                assert node_count == 1
                [pargs] = pargses
                run_process = partial(self._do_run_process, time=time, label=label.format(id=0), check=check, log_exc=log_exc, timeout=timeout)
                process = self.get_runner_process(*pargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE, **kwargs)
                interactor_kwargs['stdin'] = process.stdout
                interactor_kwargs['stdout'] = process.stdin
                yield run_process, [process]
            else:
                assert interaction_mode == IMode.FIFO

                def run(idx, pargs, from_interactor_fifo, to_interactor_fifo):
                    run_process = partial(self._do_run_process, time=time, label=label.format(id=idx), check=check, log_exc=log_exc, timeout=timeout)
                    # see note on interactors.py about having to correspond to its (and CMS's) order of FIFO opening.
                    # There should probably be an option to say whether to read the input or output first.
                    # If you can use nonblocking mode here (os.open and NONBLOCK something), that might be even better; feel free to update.
                    # But I think os.open only returns a file descriptor AND it's a Raw IO, not even a Binary (buffered) one.
                    with open(from_interactor_fifo) as from_interactor_file, open(to_interactor_fifo, 'w') as to_interactor_file:
                        return run_process(self.get_runner_process(*pargs, stdin=from_interactor_file, stdout=to_interactor_file, **kwargs))

                info_print(f"Creating {node_count} FIFO pairs")
                with tempfile.TemporaryDirectory(prefix='kg_tmp_dir_') as tmpdirname:
                    info_print("The temporary directory is", tmpdirname)
                    node_to_interactor_fifos = [os.path.join(tmpdirname, f"nod{idx}_to_itc") for idx in range(node_count)]
                    interactor_to_node_fifos = [os.path.join(tmpdirname, f"itc_to_nod{idx}") for idx in range(node_count)]
                    for fifo in chain(node_to_interactor_fifos, interactor_to_node_fifos):
                        os.mkfifo(fifo)
                        # set readable and writable by anyone
                        os.chmod(fifo, os.stat(fifo).st_mode
                                | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
                                | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)

                    # connect these fifos to the stdio's of the nodes
                    interactor_args.extend(['--from-user', *(fifo for fifo in node_to_interactor_fifos)])
                    interactor_args.extend(['--to-user',   *(fifo for fifo in interactor_to_node_fifos)])
                    yield run, range(node_count), pargses, interactor_to_node_fifos, node_to_interactor_fifos
                    info_print("Deleting temporary directory", tmpdirname)


        with prepare_communication() as (run, *argseqs), thread_pool_executor(
                    'Running interaction',
                    max_workers=min(32, node_count+1),
                    thread_name_prefix='kg_interact',
                    logf=stderr,
                ) as executor:

            itc_future = executor.submit(interactor.do_run, *interactor_args, **interactor_kwargs)
            cur_results = [*executor.map(run, *argseqs, timeout=ext_timeout)]

            return cur_results, itc_future.result()


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

