from __future__ import print_function
from compgen import *

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
}

@validator
def validate_file(file):
    lim = Bounds(bounds)

    t = file.read_int(lim.t)
    file.read_eoln()
    totaln = 0
    for cas in xrange(t):
        n = file.read_int(lim.n)
        file.read_eoln()
        totaln += n

    file.read_eof()
    ensure(totaln in lim.totaln)


if __name__ == '__main__':
    from sys import stdin
    validate_file(stdin)
