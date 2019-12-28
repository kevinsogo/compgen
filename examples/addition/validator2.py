from sys import *
from kg.validators import * ### @import

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': 1 <= +Var <= 10**5,
    'totaln': +Var <= 5*10**5,
    'a': abs(+Var) <= 10**9,
}

@validator(bounds=bounds)
def validate_file(file, *, lim):

    [t] = file.read.int(lim.t).eoln
    totaln = 0
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln
        totaln += n
        [a] = file.read.ints(n, lim.a).eoln

    [] = file.read.eof
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_file(stdin)
