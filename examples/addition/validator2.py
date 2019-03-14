from sys import *
from kg.validators import * ### @import

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': 1 <= +Var <= 10**5,
    'totaln': +Var <= 5*10**5,
    'a': abs(+Var) <= 10**9,
}

@validator()
def validate_file(file):
    lim = Bounds(bounds)

    t = file.read_int(lim.t)
    file.read_eoln()
    totaln = 0
    for cas in range(t):
        n = file.read_int(lim.n)
        totaln += n
        file.read_eoln()
        a = file.read_ints(n, lim.a)
        file.read_eoln()

    file.read_eof()
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_file(stdin)
