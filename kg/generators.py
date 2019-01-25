from io import StringIO
from random import Random

from .utils import * ### @import

@listify
def group_into(v, seq):
    ''' Group 'seq' into lists of size "v". The last group could have size < v '''
    buf = []
    for s in seq:
        buf.append(s)
        if len(buf) > v: raise Exception("v cannot be zero if seq is nonempty")
        if len(buf) == v:
            yield buf
            buf = []
    if buf:
        yield buf


class XRandom(Random):
    def shuff(self, x):
        x = list(x)
        self.shuffle(x)
        return x


# some hash on a sequence of integers. Don't change this! This is used by seed computation based on command line args.  
_pmod = 2013265921
_pbase = 1340157138
_xmod = 10**9 + 7
_xbase = 790790578
_xor = 0xDEAFBEEFEE
def _chash_seq(seq):
    pol = 0
    xol = 0
    for s in seq:
        pol = (pol * _pbase + s) % _pmod
        xol = ((xol * _xbase + s) ^ _xor) % _xmod
    return (pol << 32) ^ xol



def _write_with_validate(print_to_file, file, case_, validate=None):
    if validate is not None:
        tfile = StringIO()
        print_to_file(tfile, case_)
        validate(StringIO(tfile.getvalue())) # TODO can one read AND write on the same StringIO file?
        file.write(tfile.getvalue())
    else:
        print_to_file(file, case_)


def _make_seed(args):
    return _chash_seq(_chash_seq(map(ord, arg)) for arg in args) ^ 0xBEABDEEF


def _get_all_groups(make, distribute, args):
    # make the cases
    rand = XRandom(_make_seed(args))
    casemakers = []
    def mnew_case(*fwd_args, **info):
        def _mnew_case(f):
            nrand_seed = rand.getrandbits(64) ^ 0xC0BFEFE
            @wraps(f)
            def new_f(): # now new_f is deterministic
                return f(XRandom(nrand_seed), *fwd_args)
            casemakers.append(new_f)
            mnew_case.total_cases += 1
            for name, value in info.items(): # forward any info
                setattr(new_f, name, value)
        return _mnew_case
    mnew_case.total_cases = 0
    make(rand, mnew_case, *args)

    # distribute
    def dnew_case(*fwd_args, **info):
        def _dnew_case(f):
            nrand_seed = rand.getrandbits(64) ^ 0xC0BFEFE
            @wraps(f)
            def new_f(): # now new_f is deterministic
                return f(XRandom(nrand_seed), *fwd_args)
            for name, value in info.items(): # forward any info
                setattr(new_f, name, value)
            return new_f
        return _dnew_case
    return distribute(rand, dnew_case, casemakers, *args)


def write_nth_group_to_file(index, print_to_file, make, distribute, args, file, validate=None, single_case=False):
    '''
    Creates test case/s meant for several files, and returns the 'index'th among them. The given
    new_case decorator provides a way to ensure that only the needed cases are generated.

    print_to_file: function that prints to a file
    make: function that generates the data
    distribute: function that groups the data into separate files.
    args: arguments that will be passed to 'make', along with a random number generator.
    file: file-like object to write to.
    validate: (optional) Validate the output before printing

    Note: Ensure that `make` and `distribute` are deterministic, and any "randomness" is obtained from
    the given random number generator. This ensures reproducibility.
    '''
    groups = _get_all_groups(make, distribute, args)
    if not (0 <= index < len(groups)): raise Exception("Invalid index: {} out of {} groups".format(index, len(groups)))
    group = groups[index]() if single_case else [make() for make in groups[index]]
    _write_with_validate(print_to_file, file, group, validate=validate)
    return len(groups)

def write_to_file(print_to_file, make, args, file, validate=None):
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

    # TODO clean up this part of the code later
    def try_triple():
        try:
            make_, distribute, index = make
            return True
        except TypeError:
            return False

    if try_triple():
        make, distribute, index = make
        return write_nth_group_to_file(index, print_to_file, make, distribute, args, file, validate=validate)

    rand = XRandom(_make_seed(args))
    case_ = make(rand, *args)
    _write_with_validate(print_to_file, file, case_, validate=validate)


