from collections import defaultdict
from itertools import islice, count
from subprocess import PIPE
import json
import os.path
import re

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
    filecount, gens, settings = parse_testscript(testscript, generators, relpath=relpath)

    # get the subset of files we want to write
    files = list(islice(inputs, filecount))

    print(info_text("EXPECTING"), key_text(filecount), info_text("TEST FILES"))
    if len(files) < filecount:
        raise TestScriptError(f"{filecount} files needed but only {len(files)} input files found.")

    file_for = dict(enumerate(files, settings['start']))

    # print out the mapping of files for transparency
    prep = 5
    etced = False
    for index, (target, tfile) in enumerate(file_for.items()):
        if index < prep or index >= len(file_for.items()) - prep:
            info_print(f'*{target:>6} --> {tfile}')
        elif not etced:
            etced = True
            info_print('* ' + '.'*15)

    got_files = set()
    for gen, args, single, target, otarget, src_line in gens:
        if single:
            # single file, outputs to stdout
            filename = file_for[target]
            print(info_text(f'[o={otarget} t={target}] GENERATING'), key_text(filename),
                    info_text(f'(from {src_line!r})'))
            touch_container(filename)
            with open(filename, 'w') as file:
                gen.do_compile().do_run(*args, time=True, label='GENERATOR', stdout=file)
            got_files.add(filename)
            yield filename
        else:
            # replace the first part
            info_print(f'[o={otarget}] GENERATING MULTIPLE: {len(target)} FILES (from {src_line!r})')

            # TODO allow '$$' to appear anywhere
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

            gen.do_compile().do_run(*args, time=True, label='GENERATOR')
            assert len(sfilenames) == len(target)
            for sfile, t in zip(sfilenames, target):
                tfile = file_for[t]
                print(info_text(f"[o={otarget} t={t}] Moving {sfile} to"), key_text(tfile))
                touch_container(tfile)
                if os.path.exists(tfile): os.remove(tfile)
                os.rename(sfile, tfile)
                got_files.add(tfile)
                yield tfile

    assert got_files == set(files)


SETTING_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*\Z')
def parse_testscript(testscript, generators, *, relpath=None, **kwargs):
    found = set()
    def mex():
        return next(v for v in count(settings['start']) if v not in found)

    def validate_target(index):
        if index in found:
            raise TestScriptError(f"Duplicate target index found: {index}")
        if index < settings['start']:
            raise TestScriptError(f"Target index must be at least start={settings['start']}. Got {index}")
        found.add(index)

    gens = {}

    found_gen_args = defaultdict(list)
    def register_gen_args(line, *gen_args):
        if found_gen_args[gen_args]:
            warn_print(f'WARNING: Testscript line {line!r} will generate the same file/s as '
                       f'{found_gen_args[gen_args][-1]!r}. (Random seed is determined by args)')
        found_gen_args[gen_args].append(line)

    settings = {
        'start': 1,
    }
    settings_types = {
        'start': int,
    }
    def parse_assignment(line):
        var, delim, val = line.partition('=')
        if delim:
            assert delim == '='
            if SETTING_RE.fullmatch(var):
                return var, val

    def assign(var, val, *, parse_from_str=False):

        if parse_from_str:
            info_print(f"Testscript setting {var} = {val!r} (to be parsed)")
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                raise TestScriptError(f"Cannot parse {val!r}")

        info_print(f"Testscript setting {var} = {val!r}")

        if var not in settings:
            raise TestScriptError(f"Unknown setting: {var}")
        var_type = settings_types[var]

        if not isinstance(val, var_type):
            raise TestScriptError(f"Cannot convert {val!r} to {var_type}")

        settings[var] = val

    genlines = []
    for line in testscript.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # TODO use walrus
        assignment = parse_assignment(line)
        if assignment:
            assign(*assignment, parse_from_str=True)
        else:
            genlines.append(line)

    # assign
    for key, val in kwargs.items():
        assign(key, val)

    info_print(f"Testscript settings parsed:")
    for var, val in settings.items():
        info_print(f"* using setting {var} = {val!r}")

    later = []
    for line in genlines:
        try:
            prog, *args, pipe, target = line.split()
        except ValueError as exc:
            raise TestScriptError(f"Invalid testscript line: {line!r}")

        if pipe != '>':
            raise TestScriptError(f'Testscript line must end with "> $", "> $$", "> $count", or "> {{file/s}}": got {line!r}')

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
                count_args = ['COUNT'] + rargs
                info_print(f"Running the multifile generator {gen.filename} on {' '.join(count_args)!r} once to get the file count...")
                result = gen.do_compile().do_run(*count_args, time=True, label='GENERATOR', stdout=PIPE)
                nfiles = int(result.stdout.decode('utf-8'))
                info_print(f"Ran the multifile generator {gen.filename} on {' '.join(count_args)!r} once to get the file count...got {nfiles} files.")
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

    expected_seq = lambda: count(settings['start'])
    if sorted(found) != [*islice(expected_seq(), len(found))]:
        expected = ', '.join(map(str, islice(expected_seq(), 4)))
        raise TestScriptError(f"Some test files missing from the sequence. They must generate {expected}, ...")

    return len(found), [value for key, value in sorted(gens.items())], settings


def convert_testscript(testscript, generators, *, relpath=None, start=1):
    filecount, gens, settings = parse_testscript(testscript, generators, relpath=relpath)
    offset = start - settings['start']
    info_print(f"Testscript starts at {settings['start']}, target starts at {start}, offset is {offset}")

    for gen, args, single, target, otarget, src_line in gens:
        if src_line[0] == '!':
            warn_print(f"Warning: The following testscript line cannot be added to Polygon: '{src_line}'. Add it manually.")
        else:
            if single:
                starget = str(target + offset)
            else:
                starget = '{' + compress_t_sequence(','.join(str(t + offset) for t in target)) + '}'
            yield ' '.join([os.path.splitext(os.path.basename(gen.filename))[0], *args, '>', starget])
