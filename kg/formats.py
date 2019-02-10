from sys import stderr
from glob import glob
import re
import os.path
from itertools import count

from natsort import natsorted

class InferError(Exception): ...
class FormatError(Exception): ...

def _check_simple(x, name):
    if any(r'\*' in part for part in os.path.split(x)): raise FormatError(f"Invalid {name} pattern: {x} ... cannot handle patterns with {invalid}")

class Format:
    def __init__(self, inputg=None, outputg=None, read='', write=''):
        if not read and not write: raise FormatError("read and write modes cannot both be empty")
        if not(set(read) <= set('io')): raise FormatError(f"Unknown read mode: {read}")
        if not(set(write) <= set('io')): raise FormatError(f"Unknown write mode: {write}")
        if set(read) & set(write): raise FormatError(f"You cannot read and write at the same time: {''.join(sorted(set(read) & set(write)))}")

        self._checked = False
        self._i_re = None
        self._o_re = None

        self.inputg = inputg
        self.outputg = outputg
        self.inputs = set(glob(inputg) if inputg is not None else [])
        self.outputs = set(glob(outputg) if outputg is not None else [])

        self.i_to_o = {}
        self.o_to_i = {}

        if self.inputs and self.inputs == self.outputs:
            raise FormatError(f"Invalid patterns: {repr(inputg or '')} {repr(outputg or '')} ... They match the same files.")

        # clean up outputs.

        if self.inputs <= self.outputs: self.outputs -= self.inputs
        elif self.outputs <= self.inputs: self.inputs -= self.outputs

        if 'i' in read and not self.inputs:
            raise FormatError(f"Invalid input pattern: {inputg} ... did not match any file")
        if 'o' in read and not self.outputs:
            raise FormatError(f"Invalid output pattern: {outputg} ... did not match any file")

        if len(self.inputs) != len(self.outputs) and read and write:

            if self.outputs and len(self.inputs) != len(self.outputs):
                print(f"Warning: cannot match files {inputg} to corresponding files {outputg} (unequal number of matched files). Attempt to write anyway? [y/N]", file=stderr, end=' ')
                if input() == 'y':
                    if 'i' in read:
                        assert (read, write) == ('i', 'o')
                        self.outputs = set()
                    else:
                        assert (read, write) == ('o', 'i')
                        self.inputs = set()

            if not self.outputs and write == 'o':
                assert (read, write) == ('i', 'o')
                try:
                    self.outputs = set(map(self.infer_i_to_o, self.inputs))
                except InferError as e:
                    raise FormatError("Can't infer output file name!") from e

            if not self.inputs and write == 'i':
                assert (read, write) == ('o', 'i')
                try:
                    self.inputs = set(map(self.infer_o_to_i, self.outputs))
                except InferError as e:
                    raise FormatError("Can't infer input file name!") from e


        if self.inputs & self.outputs:
            raise FormatError(f"Invalid patterns: {repr(inputg or '')} {repr(outputg or '')} ... Some files match both.")

        if set(read) == set('io') and len(self.inputs) != len(self.outputs):
            raise FormatError(f"Invalid patterns: {repr(inputg or '')} {repr(outputg or '')} ... unequal number of files matched.")

        if read and set(read + write) == set('io'):
            # now, need to match
            for inputf in self.inputs:
                try:
                    outputf = self.infer_i_to_o(inputf)
                except InferError as e:
                    raise FormatError("Can't infer output file name for {}!".format(inputf)) from e
                if outputf not in self.outputs:
                    raise FormatError("Cannot find match for {} ... expected {}".format(inputf, outputf))
                self.i_to_o[inputf] = outputf

            for outputf in self.outputs:
                try:
                    inputf = self.infer_o_to_i(outputf)
                except InferError as e:
                    raise FormatError("Can't infer input file name for {}!".format(outputf)) from e
                if inputf not in self.inputs:
                    raise FormatError("Cannot find match for {} ... expected {}".format(outputf, inputf))
                self.o_to_i[outputf] = inputf

            assert set(self.o_to_i) <= self.outputs
            assert set(self.i_to_o) <= self.inputs
            if len(self.o_to_i) < len(self.outputs):
                missing = sorted(self.outputs - set(self.o_to_i))
                missing = ', '.join(missing) if len(missing) <= 5 else ', '.join(missing[:5] + '...')
                raise FormatError("Cannot match these output files to input files: {}".format(missing))

            if len(self.i_to_o) < len(self.inputs):
                missing = sorted(self.inputs - set(self.i_to_o))
                missing = ', '.join(missing) if len(missing) <= 5 else ', '.join(missing[:5] + '...')
                raise FormatError("Cannot match these input files to output files: {}".format(missing))

            for inputf in self.inputs:
                if inputf != self.o_to_i[self.i_to_o[inputf]]:
                    raise FormatError("{} -> {} doesn't point back! Instead, it points to {}".format(
                            inputf,
                            self.i_to_o[inputf],
                            self.o_to_i[self.i_to_o[inputf]],
                        ))

            assert set(self.o_to_i) == set(self.i_to_o.values()) == self.outputs
            assert set(self.i_to_o) == set(self.o_to_i.values()) == self.inputs

        super(Format, self).__init__()

    def _infer_parts(self, g, _re, f):
        if _re is None: raise InferError("Cannot infer: missing pattern.")
        m = _re.match(f)
        if not m: raise InferError(f"Cannot match {f} to {g}")
        return m.groups()

    def infer_iparts(self, inputf):
        self._check_patterns()
        return self._infer_parts(self.inputg, self._i_re, inputf)

    def infer_oparts(self, outputf):
        self._check_patterns()
        return self._infer_parts(self.outputg, self._o_re, outputf)

    def _join_parts(self, pat, *p):
        if pat is None: raise InferError("Cannot join: missing pattern.")
        parts = pat.split('*')
        if len(parts) != len(p) + 1: raise InferError("Cannot perform inference: unequal number of '*' parts in {} and {}.".format(self.inputg, self.outputg))
        return ''.join(a + b for a, b in zip(parts, list(p) + ['']))

    def _join_iparts(self, *p):
        return self._join_parts(self.inputg, *p)

    def _join_oparts(self, *p):
        return self._join_parts(self.outputg, *p)

    def infer_i_to_o(self, inputf):
        return self._join_oparts(*self.infer_iparts(inputf))

    def infer_o_to_i(self, outputf):
        return self._join_iparts(*self.infer_oparts(outputf))

    def _check_patterns(self):
        if not self._checked:
            if self.inputg is not None:
                _check_simple(self.inputg, 'input')
                pat = '(.*)'.join(self.inputg.replace('\\', '\\\\').replace('.', r'\.').split('*'))
                # print('Interpreting {} as regex: {}'.format(self.inputg, pat))
                self._i_re = re.compile('^' + pat + r'\Z')

            if self.outputg is not None:
                _check_simple(self.outputg, 'output')
                pat = '(.*)'.join(self.outputg.replace('\\', '\\\\').replace('.', r'\.').split('*'))
                # print('Interpreting {} as regex: {}'.format(self.outputg, pat))
                self._o_re = re.compile('^' + pat + r'\Z')

            self._checked = True

    def thru_inputs(self):
        return sorted(self.inputs)

    def thru_outputs(self):
        return sorted(self.outputs)

    def thru_io(self):
        return sorted(self.i_to_o.items())

    def thru_expected_io(self):
        for parts in self.expected_parts():
            inputf = self._join_iparts(*parts)
            outputf = self._join_oparts(*parts)
            yield inputf, outputf

    def thru_expected_inputs(self):
        for inf, outf in self.thru_expected_io():
            yield inf

    def thru_expected_outputs(self):
        for inf, outf in self.thru_expected_io():
            yield outf

###### Different formats:

formats = {}
short_format = {}
short_formats = set()
def set_format(short, *names):
    assert short not in short_formats
    short_formats.add(short)
    def _set_format(cls):
        for name in (short,) + names:
            assert name not in formats
            formats[name] = cls
            short_format[name] = short
        return cls
    return _set_format

@set_format('hr', 'hackerrank')
class HRFormat(Format):
    def __init__(self, loc='.', read='', write=''):
        super(HRFormat, self).__init__(
                os.path.join(loc, 'input', 'input*.txt'),
                os.path.join(loc, 'output', 'output*.txt'),
            read=read, write=write)
        for inputf, ex in zip(natsorted(self.inputs), self.expected_parts()):
            expinpf = self._join_iparts(*ex)
            if inputf != expinpf:
                raise FormatError("Expected {} but got {}".format(expinpf, inputf))

    @classmethod
    def expected_parts(cls):
        for c in count():
            yield str(c).zfill(2),



@set_format('pg', 'polygon')
class PGFormat(Format):
    def __init__(self, loc='.', read='', write=''):
        super(PGFormat, self).__init__(
                os.path.join(loc, 'tests', '*'),
                os.path.join(loc, 'tests', '*.a'),
            read=read, write=write)
        for inputf, ex in zip(natsorted(self.inputs), self.expected_parts()):
            expinpf = self._join_iparts(*ex)
            if inputf != expinpf:
                raise FormatError("Expected {} but got {}".format(expinpf, inputf))

    @classmethod
    def expected_parts(cls):
        for c in count(1):
            yield str(c).zfill(2),


@set_format('kg', 'kompgen')
class KGFormat(Format):
    def __init__(self, loc='.', read='', write='', tests_folder='tests'):
        super(KGFormat, self).__init__(
                os.path.join(loc, tests_folder, '*.in'),
                os.path.join(loc, tests_folder, '*.ans'),
            read=read, write=write)
        for inputf, ex in zip(natsorted(self.inputs), self.expected_parts()):
            expinpf = self._join_iparts(*ex)
            if inputf != expinpf:
                raise FormatError("Expected {} but got {}".format(expinpf, inputf))

    @classmethod
    def expected_parts(cls):
        for c in count():
            yield str(c).zfill(3),


def get_format(args, read='', write=''):
    if args.input:
        return Format(args.input, args.output, read=read, write=write)
    else:
        assert args.format
        if args.format in formats:
            return formats[args.format](args.loc, read=read, write=write)
        else:
            raise ValueError('Unrecognized format: {}'.format(args.format))

def get_format_from_type(format, loc, read='', write=''):
    return formats[format](loc, read=read, write=write)

def is_same_format(a, b):
    return short_format[a] == short_format[b]

def is_format(f, b):
    return isinstance(f, formats[b])
