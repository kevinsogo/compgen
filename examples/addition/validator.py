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

    t = file.read_int_eoln(lim.t)
    totaln = 0
    for cas in range(t):
        n = file.read_int_eoln(lim.n) # convenience method for a read_int then a read_eoln
        a = file.read_ints_eoln(n, lim.a)
        totaln += n

    file.read_eof()
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_or_detect_subtasks(validate_file, subtasks, stdin)
