import compgen

A = 10**9

def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    cases = []
    for cas in xrange(T):
        n = rand.randint(1, N)
        cases.append([rand.randint(-A, A) for i in xrange(n)])
    return cases

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout)
