"""Checks whether the input file is valid."""

from sys import *
from kg.validators import * ### @import

bounds = {
    't': 1 <= +Var <= 10**4,
    'slen': +Var == 10,
}


charset = {'R', 'B'}
@validator(bounds=bounds)
def validate(stream, *, lim):
    [t] = stream.read.int(lim.t).eoln
    for cas in range(t):
        [s] = stream.read.token(charset=charset, l=lim.slen).eoln


if __name__ == '__main__':
    validate(stdin)
