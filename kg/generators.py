from io import StringIO
from random import Random
from sys import stderr

from .utils import * ### @import

class GeneratorError(Exception): ...

@listify
def group_into(v, seq):
    ''' Group 'seq' into lists of size "v". The last group could have size < v '''
    buf = []
    for s in seq:
        buf.append(s)
        if len(buf) > v: raise ValueError("v cannot be zero if seq is nonempty")
        if len(buf) == v:
            yield buf
            buf = []
    if buf: yield buf


class KGRandom(Random):
    def shuffled(self, x):
        x = list(x)
        self.shuffle(x)
        return x
    shuff = shuffled
    def randinterval(self, a, b):
        while True:
            x = self.randint(a, b)
            y = self.randint(a, b)
            if x <= y: return x, y
    def randmerge(self, *x):
        # divide and conquer for speed
        if not x: return []
        if len(x) == 1: return list(x[0])
        return self.randmerge2(self.randmerge(*x[::2]), self.randmerge(*x[1::2]))
    def randmerge2(self, a, b):
        a = list(a)[::-1]
        b = list(b)[::-1]
        res = []
        while a or b:
            res.append((a if self.randrange(len(a) + len(b)) < len(a) else b).pop())
        return res
    def randdistrib(self, total, count, *, min_=0, max_=None, skew=1):
        if min_*count > total: raise ValueError(
                f"The total must be at least {min_}*{count}={min_*count} "
                f"when count={count} and min_={min_}")
        if max_ is not None and max_*count < total: raise ValueError(
                f"The total must be at most {max_}*{count}={max_*count} "
                f"when count={count} and max_={max_}")
        dist = [min_]*count

        inds = self.shuffled(range(count))
        for it in range(total - min_*count):
            while True:
                assert inds
                idx = min(self.randrange(len(inds)) for it in range(skew))
                inds[idx], inds[-1] = inds[-1], inds[idx]
                i = inds[-1]
                if dist[i] < max_:
                    dist[i] += 1
                    break
                else:
                    inds.pop()

        assert sum(dist) == total
        assert min_ <= min(dist) <= max(dist) <= max_

        return dist



# some hash on a sequence of integers. Don't change this! This is used by seed computation based on command line args.  
_pmod = 2013265921
_pbase = 1340157138
_xmod = 10**9 + 7
_xbase = 790790578
_xor = 0xDEAFBEEFEE
def _chash_seq(seq, *, _pmod=_pmod, _pbase=_pbase, _xmod=_xmod, _xor=_xor):
    pol = 0
    xol = 0
    for s in seq:
        pol = (pol * _pbase + s) % _pmod
        xol = ((xol * _xbase + s) ^ _xor) % _xmod
    return (pol << 32) ^ xol



def _write_with_validate(print_to_file, file, case, *, validate=None):
    if validate is not None:
        tfile = StringIO()
        print_to_file(tfile, case)
        validate(StringIO(tfile.getvalue())) # TODO can one read AND write on the same StringIO file?
        file.write(tfile.getvalue())
    else:
        print_to_file(file, case)


def _make_seed(args):
    return _chash_seq(_chash_seq(map(ord, arg)) for arg in args) ^ 0xBEABDEEF


class DistribCase:
    def __init__(self, make, distribute, *, single_case=False):
        self.make = make
        self.distribute = distribute
        self.single_case = single_case
        super().__init__()

    def lazy(self, rand, *args):
        casemakers = []
        def mnew_case(*fwd_args, **info):
            def _mnew_case(f):
                nrand_seed = rand.getrandbits(64) ^ 0xC0BFEFE
                @wraps(f)
                def new_f(): # now new_f is deterministic
                    return f(KGRandom(nrand_seed), *fwd_args)
                casemakers.append(new_f)
                mnew_case.total_cases += 1
                for name, value in info.items(): # forward any info
                    setattr(new_f, name, value)
            return _mnew_case
        mnew_case.total_cases = 0
        self.make(rand, mnew_case, *args)

        # distribute
        def dnew_case(*fwd_args, **info):
            def _dnew_case(f):
                nrand_seed = rand.getrandbits(64) ^ 0xC0BFEFE
                @wraps(f)
                def new_f(): # now new_f is deterministic
                    return f(KGRandom(nrand_seed), *fwd_args)
                for name, value in info.items(): # forward any info
                    setattr(new_f, name, value)
                return new_f
            return _dnew_case
        return self.distribute(rand, dnew_case, casemakers, *args)

    def __call__(self, rand, *args):
        return map(self.realize, self.lazy(rand, *args))

    def realize(self, group):
        return group() if self.single_case else [make() for make in group]

    def __getitem__(self, index):
        def get(rand, *args):
            groups = self.lazy(rand, *args)
            print(f"GENERATING index {index} OUT OF {len(groups)}", file=stderr) ### @if False
            if not (0 <= index < len(groups)): raise GeneratorError(f"Invalid index: {index} out of {len(groups)} groups")
            return self.realize(groups[index])
        return get

# TODO replace with write_to_file(print_to_file, make, *args, file=stdout, validate=None)
def write_to_file(print_to_file, make, args, file, *, validate=None): ### @@ if False {
    '''
    Creates test case/s meant for a single file.

    print_to_file: function that prints to a file
    make: function that generates the data
    args: arguments that will be passed to 'make', along with a random number generator.
    file: file-like object to write to.
    validate: (optional) Validate the output before printing

    Note: Ensure that `make` is deterministic, and any "randomness" is obtained from
    the given random number generator. This ensures reproducibility.
    '''
    ### @@ }
    try:
        make, distribute, index = make
    except (ValueError, TypeError):
        ...
    else:
        make = DistribCase(make, distribute)[index]

    rand = KGRandom(_make_seed(args))
    case = make(rand, *args)
    _write_with_validate(print_to_file, file, case, validate=validate) # TODO ensure this does not exit(42)


def write_to_files(print_to_file, make, filenames, *args, validate=None):
    if isinstance(filenames, str):
        filenames = file_sequence(filenames)

    try:
        make, distribute = make
    except (ValueError, TypeError):
        ...
    else:
        make = DistribCase(make, distribute)

    rand = KGRandom(_make_seed(args))
    filenames = iter(filenames)
    filecount = 0
    for index, case in enumerate(make(rand, *args)):
        try:
            filename = next(filenames)
        except StopIteration as st:
            raise GeneratorError(f"Not enough files! Need more than {index}") from st
        print("GENERATOR Writing to", filename, file=stderr) ### @if False
        with open(filename, 'w') as file:
            _write_with_validate(print_to_file, file, case, validate=validate) # TODO ensure this does not exit(42)
        filecount += 1
    print("GENERATED", filecount, "FILES", file=stderr) ### @if False
