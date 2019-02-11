from itertools import islice
from shutil import copyfile
import os.path

from .formats import *
from .iutils import *
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
            raise TestScriptError(f"{name} matches {len(progs)} programs! Please ensure that the base names of generators are unique.")
        elif not progs:
            raise TestScriptError(f"Couldn't find program {name} (from testscript). It should be in 'generators'")
        else:
            [prog] = progs
            return prog, args


def run_testscript(inputs, testscript, generators, *, relpath=None):
    info_print("PARSING TESTSCRIPT")
    filecount, gens = parse_testscript(testscript, generators, relpath=relpath)
    files = list(islice(inputs, filecount))
    if len(files) < filecount:
        raise TestScriptError(f"{filecount} files needed but only {len(files)} input files found.")

    got_files = set()
    for gen, args, single, target, otarget in gens:
        if single:
            # single file, outputs to stdout
            assert 1 <= target <= filecount
            filename = files[target - 1]
            print(info_text(f'[o={otarget} t={target}] GENERATING'), key_text(filename))
            touch_container(filename)
            gen.do_compile()
            with open(filename, 'w') as file:
                gen.do_run(*args, stdout=file)
            got_files.add(filename)
            yield filename
        else:
            # replace the first part
            info_print(f'[o={otarget}] GENERATING MULTIPLE')
            dupseq, *rargs = args
            dupseq = ':' + dupseq
            args = dupseq, *rargs
            sfilenames = list(file_sequence(dupseq))

            # clear temp
            info_print('    Preparing temp/ folder...')
            for sfile in sfilenames:
                touch_container(sfile)
                if os.path.exists(sfile):
                    if not os.path.isfile(sfile):
                        raise TestScriptError(f"Temp file {sfile} exists and is not a file! Please clear temp/")
                    else:
                        os.remove(sfile)

            gen.do_compile()
            gen.do_run(*args)
            assert len(sfilenames) == len(target)
            for sfile, t in zip(sfilenames, target):
                assert 1 <= t <= len(files)
                tfile = files[t - 1]
                print(info_text(f"[o={otarget} t={t}] Moving {sfile} to"), key_text(tfile))
                touch_container(tfile)
                if os.path.exists(tfile):
                    os.remove(tfile)
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
                later.append((gen, args))
                return

            try:
                index = int(target)
            except ValueError:
                ...
            else:
                validate_target(index)
                gens[index] = gen, args, True, index, target
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
                raise TestScriptError(f"First argument of multifile generator must generate the same sequence as target. '{dupseq}' != '{target}'")
            gens[min(indices)] = gen, args, False, indices, target

        process()

    # assign dollars
    for gen, args in later:
        index = mex()
        validate_target(index)
        gens[index] = gen, args, True, index, '$'

    if not all(i == target for i, target in enumerate(sorted(found), 1)):
        raise TestScriptError("Some test files missing from the sequence. They must generate 1, 2, 3, ...")

    return len(found), [value for key, value in sorted(gens.items())]


# TODO convert to codeforces testscript
