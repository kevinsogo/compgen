import compgen

A = 10**9

@compgen.listify
def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    for cas in xrange(T):
        n = rand.randint(1, N)
        yield [rand.randint(-A, A) for i in xrange(n)]

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    from validator import validate_file # import the validate_file function
    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout, validate=lambda f: validate_file(f, subtask=1))
