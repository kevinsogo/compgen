from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

A = 10**9

def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    cases = []
    for cas in range(T):
        n = rand.randint(1, N)
        cases.append([rand.randint(-A, A) for i in range(n)])
    return cases

if __name__ == '__main__':
    write_to_file(format_case, random_cases, argv[1:], stdout)