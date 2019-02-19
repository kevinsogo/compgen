from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

A = 10**9
def rand_case(rand, n):
    return [rand.randint(-A, A) for i in xrange(n)]

def many_cases(rand, new_case, *args):
    T, N = map(int, args[:2])
    for n in [1, N//10, N//2, 9*N//10, N]:
        for x in range(8):
            @new_case(n, x)
            def make_case(rand, n, x):
                return [rand.randrange(-A + (x + A) % 8, A+1, 8) for i in range(n)]

    while new_case.total_cases % T:
        new_case(N)(rand_case)

def distribute(rand, new_case, casemakers, *args):
    T = int(args[0])
    return group_into(T, rand.shuff(casemakers))

if __name__ == '__main__':
    index, *args = argv[1:]
    write_to_file(print_to_file, (many_cases, distribute, int(index)), args, stdout)
