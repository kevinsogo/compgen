from sys import *
from kg.validators import * ### @import

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': 1 <= +Var <= 10**5,
    'totaln': +Var <= 5*10**5,
    'a': abs(+Var) <= 10**9,
}

subtasks = {
    '1': { 'n': 1 <= +Var <= 10 },
    '2': { 'n': 1 <= +Var <= 1000 },
    '3': { },
}

@validator(bounds=bounds, subtasks=subtasks)
def validate_file(file, subtask=None, *, lim):

    [t] = file.read.int(lim.t).eoln
    totaln = 0
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln
        [a] = file.read.ints(n, lim.a).eoln
        totaln += n

    [] = file.read.eof
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_or_detect_subtasks(validate_file, subtasks, stdin)
