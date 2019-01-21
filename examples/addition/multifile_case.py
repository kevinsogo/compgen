import compgen

A = 10**9
SN = 5*10**5
def many_cases(rand, new_case, *args):
    ''' generates multiple cases that will be distributed to multiple files '''
    T, N = map(int, args[:2])
    for n in [1, N/10, N/2, 9*N/10, N]:
        for x in xrange(8):
            # generate a case where all numbers are == x mod 8
            @new_case(n, x, n=n)
            def make_case(rand, n, x):
                return [rand.randrange(-A + (x + A) % 8, A + 1, 8) for i in xrange(n)]


@compgen.listify
def distribute(rand, new_case, casemakers, *args):
    T, N = map(int, args[:2])
    def fill_up(group, totaln):
        ''' fill up the file with a bunch of cases so the total n is as close as possible to SN '''
        while len(group) < T and totaln < SN:
            n = min(N, SN - totaln)
            group.append
            @new_case(n)
            def make(rand, n):
                return [rand.randint(-A, A) for i in xrange(n)]
            totaln += n
        return group

    group = []
    totaln = 0
    for cas in rand.shuff(casemakers):
        if not (len(group) < T and totaln + cas.n <= SN):
            yield fill_up(group, totaln)
            group = []
            totaln = 0
        group.append(cas)
        totaln += cas.n
    if group: yield fill_up(group, totaln)

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_nth_group_to_file(int(argv[1]), print_to_file, many_cases, distribute, argv[2:], stdout)
