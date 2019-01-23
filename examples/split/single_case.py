from __future__ import print_function
from compgen import *
from formatter import *


A = 10**9
def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    cases = []
    for cas in xrange(T):
        n = rand.randint(1, N)
        vals = [rand.randint(-A, A) for i in xrange(rand.choice([2, int(n**.5), n/2, n, n*5]))]
        cases.append([rand.choice(vals) for i in xrange(n)])
    return cases

if __name__ == '__main__':
    from sys import argv, stdout

    write_to_file(print_to_file, random_cases, argv[1:], stdout)
