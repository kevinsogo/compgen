from kg.checkers import * ### @import

@checker.set
def get_one_input(stream, **kwargs):
    [n] = stream.read.int().eoln
    [a] = stream.read.ints(n).eoln
    return a

@checker.set
def get_output_for_input(stream, a, *, exc, **kwargs):
    [m] = stream.read.int().eoln
    [b] = stream.read.ints(m).eoln
    return b

def check_valid(a, b, exc=Exception):
    # check subsequence
    j = 0
    for i in range(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=exc)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@checker.set
def check_one(a, cont_b, judge_b, **kwargs):
    check_valid(a, cont_b, exc=Wrong)
    check_valid(a, judge_b, exc=Fail) # remove for speed
    if len(cont_b) < len(judge_b): raise Wrong("Suboptimal solution")
    if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")
    return 1.0

check = checker.make()

if __name__ == '__main__': check_files(check, title="Split")
