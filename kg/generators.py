import functools, io, random, sys

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


class KGRandom(random.Random):
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

    def randdistrib(self, total, count, *, min_=0, max_=None, skew=1): ### @@ if False {
        '''
        Generates a random partition of a number into given number of parts.

        total: number to be partitioned
        count: number of parts to partition it into
        min_: minimum size of each part
        max_: maximum size of each part
        skew: how "skewed" the partition is; higher skew means more variance

        Reasonable values for skew are from 1 to 3*count.
        '''
        ### @@ }
        if min_*count > total:
            raise ValueError(f"The total must be at least {min_}*{count}={min_*count} when count={count} and min_={min_}")
        if max_ is not None and max_*count < total:
            raise ValueError(f"The total must be at most {max_}*{count}={max_*count} when count={count} and max_={max_}")
        if skew <= 0:
            raise ValueError("The skew has to be at least 1.")
        if max_ is None:
            max_ = total
        dist = [min_]*count

        inds = self.shuffled(range(count))
        for it in range(total - min_*count):
            while True:
                assert inds
                idx = min(self.randrange(len(inds)) for it in range(skew))
                # TODO optimize this part. It will be backwards incompatible, so we can only do it in the next "version".
                if dist[inds[idx]] < max_:
                    dist[inds[idx]] += 1
                    break
                else:
                    # TODO this somehow destroys the distribution, so this whole function needs a better implementation.
                    # for now, this will do.
                    inds[idx], inds[-1] = inds[-1], inds[idx]
                    inds.pop()

        assert sum(dist) == total
        assert min_ <= min(dist) <= max(dist) <= max_

        return dist

    @listify
    def randpartition(self, total, min_=1, skew=2): ### @@ if False {
        '''
        Generates a random partition of a number into a random number of parts.
        Default options make the result uniformly distributed over all such
        partitions.

        total: number to be partitioned
        min_: minimum size of each part
        skew: how "skewed" the partition is; higher skew means larger part size

        Reasonable values of skew are from 2 to total. The average size of each
        part except the last is min_ + skew - 1. More specifically, the
        distribution of part size is a negative binomial distribution with
        r = 1 and p = (skew - 1)/skew, using the parametrization on Wikipedia.
        '''
        ### @@ }
        if total < 0: raise ValueError("The total should be at least 0.")
        if min_ <= 0: raise ValueError("The value of min_ should be at least 1.")
        if skew <= 0: raise ValueError("The skew should be at least 1.")
        if total == 0:
            return []

        it = 0
        for i in range(total - min_):
            it += 1
            if it >= min_ and not self.randrange(skew):
                yield it
                it = 0
        yield it + min_



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


def _make_seed(args):
    return _chash_seq(_chash_seq(map(ord, arg)) for arg in args) ^ 0xBEABDEEF


def _write_with_validate(format_case, file, case, *, validate=None):
    if validate is not None:
        tfile = io.StringIO()
        format_case(tfile, case)
        tfile.seek(0) # reset the StringIO
        validate(tfile)
        file.write(tfile.getvalue())
    else:
        format_case(file, case)


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
                @functools.wraps(f)
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
                @functools.wraps(f)
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
            print(f"[G] Generating file index {index} of {len(groups)}", file=sys.stderr) ### @if False
            if not (0 <= index < len(groups)): raise GeneratorError(f"Invalid index: {index} of {len(groups)} groups")
            return self.realize(groups[index])
        return get

# TODO replace with write_to_file(format_case, make, *args, file=stdout, validate=None) (maybe? maybe not?) ### @if False
def write_to_file(format_case, make, args, file, *, validate=None): ### @@ if False {
    '''
    Creates test case/s meant for a single file.

    format_case: function that prints to a file
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
    _write_with_validate(format_case, file, case, validate=validate) # TODO ensure this does not exit(42)


def write_to_files(format_case, make, filenames, *args, validate=None):
    try:
        make, distribute = make
    except (ValueError, TypeError):
        ...
    else:
        make = DistribCase(make, distribute)

    rand = KGRandom(_make_seed(args))

    if filenames == "COUNT":
        print(sum(1 for case in make(rand, *args)))
        return

    if isinstance(filenames, str):
        filenames = file_sequence(filenames, mktemp=True)
    filenames = iter(filenames)
    filecount = 0
    for index, case in enumerate(make(rand, *args)):
        try:
            filename = next(filenames)
        except StopIteration as st:
            raise GeneratorError(f"Not enough files! Need more than {index}") from st
        print("[G] Generator writing to", filename, file=sys.stderr) ### @if False
        with open(filename, 'w') as file:
            _write_with_validate(format_case, file, case, validate=validate) # TODO ensure this does not exit(42)
        filecount += 1
    print("[G] Generated", filecount, "files", file=sys.stderr) ### @if False
