from __future__ import print_function
from compgen import *
from formatter import *
from validator import *

A = 10**9

@listify
def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    for cas in xrange(T):
        n = rand.randint(1, N)
        yield [rand.randint(-A, A) for i in xrange(n)]

if __name__ == '__main__':
    from sys import argv, stdout

    write_to_file(print_to_file, random_cases, argv[1:], stdout,
            validate=lambda f: validate_file(f, subtask=1))
