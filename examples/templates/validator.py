from __future__ import print_function
from compgen import *

subtasks = {
    '1': { 'n': Interval(1, 10) },
    '2': { 'n': Interval(1, 1000) },
    '3': { },
}

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
}

@validator
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    ... # validate here as usual

if __name__ == '__main__':
    from sys import stdin, argv
    subtask = argv[1] if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
