from __future__ import print_function
from compgen import *

subtasks = {
    1: {
        'n': Interval(1, 10),
    },
    2: {
        'n': Interval(1, 1000),
    },
    3: {
    },
}

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
    'a': Interval(-10**9, 10**9),
}

@validator
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    t = file.read_int(lim.t)
    file.read_eoln()
    totaln = 0
    for cas in xrange(t):
        n = file.read_int(lim.n)
        totaln += n
        file.read_eoln()
        a = []
        for i in xrange(n):
            a.append(file.read_int(lim.a))
            (file.read_space if i < n - 1 else file.read_eoln)()

    file.read_eof()
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    from sys import stdin, argv
    subtask = argv[1] if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
