from sys import *
from kg.validators import * ### @import

bounds = {
    'n': abs(+Var) <= 10**9,
    'm': 1 <= +Var <= 100,
}

@validator(bounds=bounds)
def validate(stream, *, lim):
    [n, m] = stream.read.int(lim.n).space.int(lim.m).eoln.eof

if __name__ == '__main__':
    validate(stdin)
