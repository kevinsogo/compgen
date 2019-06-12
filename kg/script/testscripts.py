from collections import defaultdict
from itertools import islice, count
from shutil import copyfile
from subprocess import PIPE
import os.path

from .formats import *
from .programs import *
from .utils import *

class TestScriptError(Exception): ...

def find_matches(cmd, generators):
    for prog in generators:
        if prog.matches_abbr(cmd):
            yield prog

def parse_generator(name, *args, generators, relpath=None):
    if name == '!':
        return Program.from_args('', args, relpath=relpath), []
    else:
        progs = list(find_matches(name, generators))
        if len(progs) >= 2:
            raise TestScriptError(f"{name} matches {len(progs)} programs! Please ensure that the base names of "
                    "generators are unique.")
        elif not progs:
            raise TestScriptError(f"Couldn't find program {name} (from testscript). It should be in 'generators'")
        else:
            [prog] = progs
            return prog, args


def run_testscript(inputs, testscript, generators, *, relpath=None):
    info_print("PARSING TESTSCRIPT")
    filecount, gens = parse_testscript(testscript, generators, relpath=relpath)
    files = list(islice(inputs, filecount))
    info_print(f"EXPECTING {filecount} TEST FILES")
    if len(files) < filecount:
        raise TestScriptError(f"{filecount} files needed but only {len(files)} input files found.")

    got_files = set()
    for gen, args, single, target, otarget, src_line in gens:
        if single:
            # single file, outputs to stdout
            assert 1 <= target <= filecount
            filename = files[target - 1]
            print(info_text(f'[o={otarget} t={target}] GENERATING'), key_text(filename),
                    info_text(f'(from {src_line!r})'))
            touch_container(filename)
            with open(filename, 'w') as file:
                gen.do_compile().do_run(*args, stdout=file)
            got_files.add(filename)
            yield filename
        else:
            # replace the first part
            info_print(f'[o={otarget}] GENERATING MULTIPLE: {len(target)} FILES (from {src_line!r})')
            dupseq, *rargs = args
            dupseq = ':' + dupseq
            args = dupseq, *rargs
            sfilenames = [attach_relpath(relpath, sfile) for sfile in file_sequence(dupseq)]

            # clear temp
            temp_folder = attach_relpath(relpath, os.path.join('temp', ''))
            info_print(f'    Preparing the {temp_folder} folder...')
            for sfile in sfilenames:
                touch_container(sfile)
                if os.path.exists(sfile):
                    if not os.path.isfile(sfile):
                        raise TestScriptError(f"Temp file {sfile} exists and is not a file! Please clear {temp_folder}")
                    os.remove(sfile)

            gen.do_compile().do_run(*args)
            assert len(sfilenames) == len(target)
            for sfile, t in zip(sfilenames, target):
                assert 1 <= t <= len(files)
                tfile = files[t - 1]
                print(info_text(f"[o={otarget} t={t}] Moving {sfile} to"), key_text(tfile))
                touch_container(tfile)
                if os.path.exists(tfile): os.remove(tfile)
                os.rename(sfile, tfile)
                got_files.add(tfile)
                yield tfile

    assert got_files == set(files)


def parse_testscript(testscript, generators, *, relpath=None):
    found = set()
    def mex(start=1):
        return next(v for v in count(start) if v not in found)

    def validate_target(index):
        if index in found:
            raise TestScriptError(f"Duplicate target index found: {index}")
        if index < 1:
            raise TestScriptError(f"Target index must be positive. Got {index}")
        found.add(index)

    gens = {}

    found_gen_args = defaultdict(list)
    def register_gen_args(line, *gen_args):
        if found_gen_args[gen_args]:
            warn_print(f'WARNING: Testscript line {line!r} will generate the same file/s as '
                       f'{found_gen_args[gen_args][-1]!r}. (Random seed is determined by args)')
        found_gen_args[gen_args].append(line)
    later = []
    for line in testscript.strip().split('\n'):
        parts = line.split()
        if not parts or parts[0] == '#':
            continue
        try:
            prog, *args, pipe, target = parts
        except ValueError as exc:
            raise TestScriptError(f"Invalid testscript line: {line!r}")

        if pipe != '>':
            raise TestScriptError(f'Testscript line must end with "> $" or "> {{file/s}}": got {line!r}')

        gen, args = parse_generator(prog, *args, generators=generators, relpath=relpath)

        def process():
            if target.startswith('$'):
                later.append((gen, args, line, target))
                return

            try:
                index = int(target)
            except ValueError:
                ...
            else:
                validate_target(index)
                register_gen_args(line, gen, *args)
                gens[index] = gen, args, True, index, target, line
                return

            if not (target.startswith('{') and target.endswith('}')):
                raise TestScriptError(f"Invalid target file sequence: {target!r}")
            indices = list_t_sequence(target[1:-1])
            if not indices:
                raise TestScriptError(f"Empty file sequence: {target!r}")
            for index in indices:
                validate_target(index)
            dupseq, *rargs = args
            if list(t_sequence(dupseq)) != indices:
                raise TestScriptError("First argument of multifile generator must generate the same sequence as target. "
                        f"{dupseq!r} != {target!r}")
            register_gen_args(line, gen, *rargs)
            gens[min(indices)] = gen, args, False, indices, target, line

        process()

    # assign dollars
    for gen, args, src_line, target in later:
        if target == '$':
            index = mex()
            validate_target(index)
            register_gen_args(src_line, gen, *args)
            gens[index] = gen, args, True, index, target, src_line
        else:
            dupseq, *rargs = args
            if dupseq != '$$':
                raise TestScriptError("First argument of multifile generator with dollar target must be $$. "
                        f"{dupseq!r} != $$")

            if target == "$$":
                result = gen.do_compile().do_run("COUNT", *rargs, stdout=PIPE)
                nfiles = int(result.stdout.decode('utf-8'))
            else:
                try:
                    nfiles = int(target[1:])
                except ValueError:
                    raise TestScriptError(f"Invalid dollar target: {target!r}")

            indices = []
            for file in range(nfiles):
                index = mex()
                validate_target(index)
                indices.append(index)
            register_gen_args(src_line, gen, *rargs)
            rtarget = compress_t_sequence(','.join(map(str, indices)))
            target = '{' + rtarget + '}'
            args = rtarget, *rargs
            gens[min(indices)] = gen, args, False, indices, target, src_line

    if not all(i == target for i, target in enumerate(sorted(found), 1)):
        raise TestScriptError("Some test files missing from the sequence. They must generate 1, 2, 3, ...")

    return len(found), [value for key, value in sorted(gens.items())]


def convert_testscript(testscript, generators, *, relpath=None):
    filecount, gens = parse_testscript(testscript, generators, relpath=relpath)

    for gen, args, single, target, otarget, src_line in gens:
        if src_line[0] != '!':
            yield ' '.join([gen.filename, *args, '>', otarget])
