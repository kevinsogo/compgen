from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

A = 10**9
def gen_single(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    cases = []
    for cas in range(T):
        n = rand.randint(1, N)
        vals = [rand.randint(-A, A) for i in range(rand.choice([2, int(n**.5), n//2, n, n*5]))]
        cases.append([rand.choice(vals) for i in range(n)])
    return cases

if __name__ == '__main__':
    write_to_file(format_case, gen_single, argv[1:], stdout)
