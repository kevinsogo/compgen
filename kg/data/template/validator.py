from sys import *
from kg.validators import * ### @import

subtasks = {
    '1': { },
    '2': { },
    '3': { },
}

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
}

@validator
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    ... # write your validator here

    # file .read_int(), .read_ints(), .read_space(), .read_eoln(), etc.
    # file.read_eof()

if __name__ == '__main__':
    subtask = argv[1] if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
