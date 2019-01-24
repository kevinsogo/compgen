from __future__ import print_function
from compgen import *
from formatter import *

A = 10**9

def random_cases(rand, *args):
    T, N = map(int, args[:2])
    cases = []
    for cas in xrange(T):
        n = rand.randint(1, N)
        cases.append([rand.randint(-A, A) for i in xrange(n)])
    return cases

if __name__ == '__main__':
    from sys import argv, stdout

    write_to_file(print_to_file, random_cases, argv[1:], stdout)
