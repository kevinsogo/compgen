import compgen

A = 10**9
def make_case(rand, n):
    return [rand.randint(-A, A) for i in xrange(n)]

def many_cases(rand, new_case, *args):
    ''' generates multiple cases that will be distributed to multiple files '''
    T, N = map(int, args[:2])
    for n in [1, N/10, N/2, 9*N/10, N]:
        for x in xrange(8):
            # generate a case where all numbers are == x mod 8
            @new_case(n, x)
            def make_case(rand, n, x):
                return [rand.randrange(-A + (x + A) % 8, A+1, 8) for i in xrange(n)]

    while new_case.total_cases % T:
        new_case(N)(make_case)


def distribute(rand, new_case, casemakers, *args):
    T, N = map(int, args[:2])
    return compgen.group_into(T, rand.shuff(casemakers)) # shuffle and then divide into groups of size T

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_nth_group_to_file(int(argv[1]), print_to_file, many_cases, distribute, argv[2:], stdout)

