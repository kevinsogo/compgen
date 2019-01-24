from __future__ import print_function, division, unicode_literals, absolute_import
from compgen.checkers import *

def get_sequence(file, exc):
    try:
        m = int(file.next().rstrip())
        b = map(int, file.next().rstrip().split(' ')) # stricter
    except Exception as e:
        raise exc("Failed to get a sequence: " + str(e))
    ensure(len(b) == m, lambda: "Expected {} numbers but got {}".format(m, len(b)), exc=exc)
    return b

def is_subsequence(a, b):
    ... # code omitted

def check_valid(a, b, exc):
    ensure(is_subsequence(a, b), "Not a subsequence!", exc=exc)
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@set_checker(no_extra_chars=True)
def check_solution(input_file, output_file, judge_file, **kwargs):
    z = int(input_file.next())
    for cas in xrange(z):
        n = int(input_file.next())
        a = map(int, input_file.next().strip().split())
        ensure(len(a) == n, "Judge input invalid", exc=Fail)
        cont_b = get_sequence(output_file, WA)
        judge_b = get_sequence(judge_file, Fail)
        check_valid(a, cont_b, WA)
        check_valid(a, judge_b, Fail)
        if len(cont_b) < len(judge_b): raise WA("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

    return 1.0

if __name__ == '__main__': chk()
