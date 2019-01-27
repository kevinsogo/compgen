from sys import *
from kg.validators import * ### @import

subtasks = {
    '1': { 'n': Interval(1, 10) },
    '2': { 'n': Interval(1, 1000) },
    '3': { },
}

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
    'a': Interval(-10**9, 10**9),
}

@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    t = file.read_int_eoln(lim.t)
    totaln = 0
    for cas in range(t):
        n = file.read_int_eoln(lim.n)
        a = file.read_ints_eoln(n, lim.a)
        totaln += n

    file.read_eof()
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    subtask = argv[1] if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
