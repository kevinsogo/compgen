from collections import defaultdict, namedtuple
from itertools import islice, count
from subprocess import PIPE
import concurrent.futures
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

def _get_generator(name, *args, generators, relpath=None):
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

TestScriptLineSetting = namedtuple('TestScriptLineSetting', ['src_line', 'var', 'val'])
TestScriptLineGen = namedtuple('TestScriptLineGen', ['src_line', 'prog', 'args', 'target'])
TestScriptGenData = namedtuple('TestScriptGenData', ['src_line', 'gen', 'args', 'target'])
TestScriptGen = namedtuple('TestScriptGen', ['src_line', 'gen', 'args', 'single', 'target_indices', 'target', 'dollar_loc', 'rem_args', 'rep_args'])
TestScript = namedtuple('TestScript', ['src', 'file_count', 'gens', 'start'])

def run_testscript(inputs, testscript_src, generators, *, relpath=None, validator=None, max_workers=None):
    info_print("PARSING TESTSCRIPT")
    ts = compile_testscript(testscript_src, generators, relpath=relpath, max_workers=max_workers)

    # get the subset of files we want to write
    files = [*islice(inputs, ts.file_count)]

    print(info_text("EXPECTING"), key_text(ts.file_count), info_text("TEST FILES"))
    if len(files) < ts.file_count:
        raise TestScriptError(f"{ts.file_count} files needed but only {len(files)} input files found.")

    file_for = dict(enumerate(files, ts.start))

    # print out the mapping of files for transparency
    prep = 5
    etced = False
    for index, (target, tfile) in enumerate(file_for.items()):
        if index < prep or index >= len(file_for.items()) - prep:
            info_print(f'*{target:>6} --> {tfile}')
        elif not etced:
            etced = True
            info_print('* ' + '.'*15)

    def pref_r(gen):
        return compress_t_sequence(','.join(map(str, gen.target_indices))) + ":"

    def pref_v(index):
        return str(index) + ":"

    mxl = max(
            max(len(pref_r(gen)) for gen in ts.gens),
            max(len(pref_v(index)) for gen in ts.gens for index in gen.target_indices),
        ) + 2
    @listify
    def run_testscript_line(gen):
        def pref(print, *args, **kwargs):
            info_print(pref_r(gen).rjust(mxl), end=' ')
            print(*args, **kwargs)
        pref(print, src_text(repr(gen.src_line)), info_text('starting'))
        if gen.single:
            # single file, outputs to stdout
            [index] = gen.target_indices
            filename = file_for[index]
            touch_container(filename)
            with open(filename, 'w') as file:
                gen.gen.do_run(*gen.args, label='GENERATOR', stdout=file)
            pref(print, key_text(filename), info_text(f'generated  [line {gen.src_line!r}]'))
            yield filename, index
        else:
            pref(info_print, f'Generating {len(gen.target_indices)} files')

            starget = ':' + compress_t_sequence(','.join(map(str, gen.target_indices)))
            sfilenames = [attach_relpath(relpath, sfile) for sfile in file_sequence(starget)]

            # clear temp
            temp_folder = attach_relpath(relpath, os.path.join('temp', ''))
            pref(info_print, f'Preparing the {temp_folder} folder...')
            for sfile in sfilenames:
                touch_container(sfile)
                if os.path.exists(sfile):
                    if not os.path.isfile(sfile):
                        raise TestScriptError(f"Temp file {sfile} exists and is not a file! Please clear {temp_folder}")
                    os.remove(sfile)

            gen.gen.do_run(*gen.rep_args(starget), label='GENERATOR')
            assert len(sfilenames) == len(gen.target_indices)
            for sfile, t in zip(sfilenames, gen.target_indices):
                tfile = file_for[t]
                pref(print, key_text(tfile), info_text(f"<-- {sfile} (moved)  [line {gen.src_line!r}]"))
                touch_container(tfile)
                if os.path.exists(tfile): os.remove(tfile)
                os.rename(sfile, tfile)
                yield tfile, t

        # pref(info_print, f'{gen.src_line!r} done')
        if max_workers == 1: print()

    with thread_pool_executor(
                "Compiling programs",
                max_workers=max_workers,
                thread_name_prefix="kg_compile_progs",
            ) as executor:
        for gen in {gen.gen for gen in ts.gens}:
            executor.submit(gen.do_compile)
        if validator:
            executor.submit(validator.do_compile)

    def validate(filename, index):
        def pref(print, *args, **kwargs):
            info_print(pref_v(index).rjust(mxl), end=' ')
            print(*args, **kwargs)
        if validator:
            pref(info_print, f'{filename!r} validating...')
            with open(filename) as file:
                validator.do_run(stdin=file, check=True, label='VALIDATOR')
            pref(info_print, f'{filename!r} validated')
            if max_workers == 1: print()
        return filename

    def run_and_start_validation(gen):
        return [executor.submit(validate, file, index) for file, index in run_testscript_line(gen)]

    with thread_pool_executor(
                "Running testscript",
                max_workers=max_workers,
                thread_name_prefix="kg_run_testscript",
            ) as executor:
        validate_futures = [
            future
            for futures in wait_all(
                (executor.submit(run_and_start_validation, gen) for gen in ts.gens),
                "generate files",
                executor=executor,
                logf=stdout,
            )
            for future in futures
        ]
        got_files = wait_all(validate_futures, "validate files", executor=executor, logf=stdout)

        assert len(set(got_files)) == len(got_files), (got_files, files)
        assert set(got_files) == set(files), (got_files, files)
        return got_files

SETTING_RE = re.compile(r'^(?P<var>[a-zA-Z][a-zA-Z0-9_]*)=(?P<val>.+)\Z')
GEN_RE = re.compile(r'^(?P<prog>[a-zA-Z!][a-zA-Z0-9_.]*) (?P<args>.*)\>\s*(?P<target>\{?\$?\$?[,0-9-]*\}?)\Z')
def _parse_testscript_lines(testscript, *, max_workers=None):
    for src_line in testscript.splitlines():
        line = src_line.strip()
        if not line:
            continue

        # TODO walrus
        match = SETTING_RE.fullmatch(line)
        if match:
            yield TestScriptLineSetting(src_line=src_line, **match.groupdict())
            continue

        match = GEN_RE.fullmatch(line)
        if match:
            yield TestScriptLineGen(src_line=src_line, **match.groupdict())
            continue

        raise TestScriptError(f"Cannot parse testscript line {src_line!r}")


def _get_settings(setting_lines, *, max_workers=None, **override_settings):
    settings = {
        'start': 1,
    }
    settings_types = {
        'start': int,
    }
    def assign(var, val):
        info_print(f"Testscript setting {var} = {val!r}")

        if var not in settings:
            raise TestScriptError(f"Unknown setting: {var}")

        var_type = settings_types[var]
        if not isinstance(val, var_type):
            raise TestScriptError(f"Cannot convert {val!r} to {var_type}")

        settings[var] = val

    # assign settings
    for line in setting_lines:
        info_print(f"Testscript setting {line.src_line!r} (to be parsed)")
        try:
            val = json.loads(line.val)
        except json.JSONDecodeError:
            raise TestScriptError(f"Cannot parse {line.val!r}")
        assign(line.var, val)

    # assign override_settings (takes priority over settings in testscript)
    for key, val in override_settings.items():
        assign(key, val)

    info_print(f"Testscript settings parsed:")
    for var, val in settings.items():
        info_print(f"* using setting {var} = {val!r}")

    return settings


def _get_gens(settings, gen_lines, generators, *, relpath=None, max_workers=None):


    # get the generator programs and split the args
    def _get_gen_data():
        for line in gen_lines:
            gen, args = _get_generator(line.prog, *line.args.split(), generators=generators, relpath=relpath)
            yield TestScriptGenData(
                    src_line=line.src_line,
                    gen=gen,
                    args=tuple(args),
                    target=line.target,
                )

    # move the dollared lines to the end
    # Note: 'sorted' is stable
    gen_data = sorted(_get_gen_data(), key=lambda line: line.target.startswith('$'))



    # compile the multifile generators
    with thread_pool_executor(
                "Compiling programs",
                max_workers=max_workers,
                thread_name_prefix="kg_compile_progs",
            ) as executor:
        for gen in {gend.gen for gend in gen_data if gend.target == '$$'}:
            executor.submit(gen.do_compile)


    def get_dollar_loc(*args):
        try:
            dollar_loc = next(i for i, arg in enumerate(args) if arg.endswith('$$'))
        except StopIteration:
            raise TestScriptError(
                    f"At least one argument of multifile generator with dollar target must end with $$. got {args}",
                )

        assert 0 <= dollar_loc < len(args)
        assert args[dollar_loc].endswith('$$')
        rem_args = tuple(arg for i, arg in enumerate(args) if i != dollar_loc)
        rep_args = lambda rep: [(arg[:-2] + rep if i == dollar_loc else arg) for i, arg in enumerate(args)] # TODO removesuffix
        return dollar_loc, rem_args, rep_args



    def get_file_info(gend):
        # try if single-file fixed
        try:
            index = int(gend.target)
        except ValueError:
            ...
        else:
            return True, [index], 0

        # try if multi-file fixed
        if gend.target.startswith('{') and gend.target.endswith('}'):
            # TODO removeprefix and removesuffix
            indices = list_t_sequence(gend.target[1:-1])
            if not indices:
                raise TestScriptError(f"Empty file sequence: {gend.target!r}")
            return False, indices, 0

        # try if single-file dollar
        if gend.target == '$':
            return True, [], 1

        # try if multi-file double dollar
        if gend.target == '$$':
            dollar_loc, rem_args, rep_args = get_dollar_loc(*gend.args)
            count_args = rep_args('COUNT')
            info_print(f"Running the multifile generator {gend.gen.filename} on {' '.join(count_args)!r} once to get the file count...")
            result = gend.gen.do_run(*count_args, label='GENERATOR', stdout=PIPE)
            nfiles = int(result.stdout.decode('utf-8'))
            info_print(f"Ran the multifile generator {gend.gen.filename} on {' '.join(count_args)!r} once to get the file count...got {nfiles} files.")
            if nfiles <= 0:
                raise TestScriptError(f"Invalid file count {nfiles}; must be positive")
            return False, [], nfiles
        
        # try if multi-file single dollar
        if gend.target.startswith('$'):
            try:
                nfiles = int(gend.target[1:]) # TODO removeprefix
            except ValueError:
                raise TestScriptError(f"Invalid multifile dollar target: {gend.target!r}")
            else:
                if nfiles <= 0:
                    raise TestScriptError(f"Invalid file count {nfiles}; must be positive")
                return False, [], nfiles

        # I don't know what this line is
        raise TestScriptError(f"Invalid target: {gend.target!r}")


    # compute file counts. do this before assigning dollars to avoid concurrency issues
    gen_data = [*thread_pool_executor(
            "Getting file counts of multifile generators",
            max_workers=max_workers,
            thread_name_prefix="kg_get_multifile_counts",
        ).map((lambda g: (g, *get_file_info(g))), gen_data)]

    found_indices = set()
    found_args = defaultdict(list)
    def mex_indices(n=1):
        return islice((v for v in count(settings['start']) if v not in found_indices), n)

    # assign indices, with the non-dollared lines first
    gens = []
    for gend, single, indices, extra in gen_data:

        # compute the extra indices
        indices += mex_indices(extra)
        del extra

        # verify counts
        if single:
            assert len(indices) == 1
            dollar_loc = None
            args = rem_args = gend.args
            rep_args = None
        else:
            assert len(indices) >= 1
            dollar_loc, rem_args, rep_args = get_dollar_loc(*gend.args)
            args = rep_args(compress_t_sequence(','.join(map(str, indices))))

        # build the gen
        gen = TestScriptGen(
                src_line=gend.src_line,
                gen=gend.gen,
                args=args,
                single=single,
                target_indices=indices,
                target=gend.target,
                dollar_loc=dollar_loc,
                rem_args=rem_args,
                rep_args=rep_args,
            )
        gens.append(gen)
        del args, single, indices, dollar_loc, rem_args, rep_args

        # warn for duplicate argument list
        fargs = gen.gen, gen.rem_args
        if found_args[fargs]:
            warn_print(f'WARNING: Testscript line {gen.src_line!r} will generate the same file/s as '
                       f'{found_args[fargs][-1]!r}. (Random seed is determined by args)')
        found_args[fargs].append(gen.src_line)

        # error if an index has already appeared
        for index in gen.target_indices:
            if index < settings['start']:
                raise TestScriptError(f"Target index must be at least start={settings['start']}; got {index}")
            if index in found_indices:
                raise TestScriptError(f"Duplicate target index found: {index}")
            found_indices.add(index)

    # sort the gens by their minimum target index
    gens.sort(key=lambda gen: min(gen.target_indices))

    for gen in gens:
        info_print(f"Line {gen.src_line!r}: {gen.gen.filename!r} with {len(gen.target_indices)} files: {gen.target_indices}")


    return gens, found_indices


def compile_testscript(testscript_src, generators, *, relpath=None, max_workers=None, **kwargs):

    # split testscript into lines
    setting_lines = []
    gen_lines = []
    for line in _parse_testscript_lines(testscript_src, max_workers=max_workers):
        if isinstance(line, TestScriptLineSetting):
            setting_lines.append(line)
        elif isinstance(line, TestScriptLineGen):
            gen_lines.append(line)
        else:
            raise TestScriptError(f"Testscript line {line} has unknown type")

    # process the setting lines
    settings = _get_settings(setting_lines, max_workers=max_workers, **kwargs)

    # process the gen lines
    gens, found_indices = _get_gens(settings, gen_lines, generators, relpath=relpath, max_workers=max_workers)

    # check that everything went right
    assert len(found_indices) >= len(gens) == len(gen_lines)
    assert sorted(set(found_indices)) == sorted(found_indices) == sorted(t for gen in gens for t in gen.target_indices)

    # check that the sequence of files is correct
    expected_seq = lambda: count(settings['start'])
    if sorted(found_indices) != [*islice(expected_seq(), len(found_indices))]:
        expected_s = ', '.join(map(str, islice(expected_seq(), 4)))
        raise TestScriptError(
                f"Some test files missing from the sequence. "
                f"They must generate [{expected_s}, ...] (got {sorted(found_indices)})")

    return TestScript(src=testscript_src, file_count=len(found_indices), gens=gens, **settings)


def transpile_testscript_pg(testscript_src, generators, *, relpath=None, start=1, max_workers=None):
    ts = compile_testscript(testscript_src, generators, relpath=relpath, max_workers=max_workers)
    offset = start - ts.start
    info_print(f"Testscript starts at {ts.start}, target starts at {start}, offset is {offset}")

    for gen in ts.gens:
        if gen.src_line[0] == '!':
            warn_print(f"Warning: The following testscript line cannot be added to Polygon: '{gen.src_line}'. Add it manually.")
        else:
            if gen.single:
                [t] = gen.target_indices
                starget = str(t + offset)
                args = gen.rem_args
            else:
                starget = compress_t_sequence(','.join(str(t + offset) for t in gen.target_indices))
                args = gen.rep_args(starget)
                starget = '{' + starget + '}'
                
            gen_base, gen_ext = os.path.splitext(os.path.basename(gen.gen.filename))
            yield ' '.join([gen_base, *args, '>', starget])