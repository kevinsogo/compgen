from collections import defaultdict
from itertools import islice
from shutil import copyfile
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
                    info_text(f'(from {repr(src_line)})'))
            touch_container(filename)
            with open(filename, 'w') as file:
                gen.do_compile().do_run(*args, stdout=file)
            got_files.add(filename)
            yield filename
        else:
            # replace the first part
            info_print(f'[o={otarget}] GENERATING MULTIPLE: {len(target)} FILES (from {repr(src_line)})')
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
    def mex():
        v = 1
        while v in found: v += 1
        return v

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
            warn_print(f'WARNING: Testscript line {repr(line)} will generate the same file/s as '
                       f'{repr(found_gen_args[gen_args][-1])}. (Random seed is determined by args)')
        found_gen_args[gen_args].append(line)
    later = []
    for line in testscript.strip().split('\n'):
        parts = line.split()
        if not parts or parts[0] == '#':
            continue
        try:
            prog, *args, pipe, target = parts
        except ValueError as exc:
            raise TestScriptError(f"Invalid testscript line: {repr(line)}")

        if pipe != '>':
            raise TestScriptError(f'Testscript line must end with "> $" "> {{file/s}}": {repr(line)}') from exc

        gen, args = parse_generator(prog, *args, generators=generators, relpath=relpath)

        def process():
            if target == '$':
                later.append((gen, args, line))
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
                raise TestScriptError(f"Invalid target file sequence: {repr(target)}")
            indices = list_t_sequence(target[1:-1])
            if not indices:
                raise TestScriptError(f"Empty file sequence: {target}")
            for index in indices:
                validate_target(index)
            dupseq, *rargs = args
            if list(t_sequence(dupseq)) != indices:
                raise TestScriptError("First argument of multifile generator must generate the same sequence as target. "
                        f"'{dupseq}' != '{target}'")
            register_gen_args(line, gen, *rargs)
            gens[min(indices)] = gen, args, False, indices, target, line

        process()

    # assign dollars
    for gen, args, src_line in later:
        index = mex()
        validate_target(index)
        register_gen_args(src_line, gen, *args)
        gens[index] = gen, args, True, index, '$', src_line

    if not all(i == target for i, target in enumerate(sorted(found), 1)):
        raise TestScriptError("Some test files missing from the sequence. They must generate 1, 2, 3, ...")

    return len(found), [value for key, value in sorted(gens.items())]


# TODO convert to codeforces testscript
