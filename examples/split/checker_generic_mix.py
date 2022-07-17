from validator import * ### @import
from kg.checkers import * ### @import

lim = Bounds(bounds) & Bounds({'m': +Var >= 0})

def get_sequence(stream, exc=Exception):
    [m] = stream.read.int(lim.m).eoln
    [b] = stream.read.ints(m, lim.a).eoln
    return b

def check_valid(a, b, exc=Exception):
    # check subsequence
    j = 0
    for i in range(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=exc)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@checker('tokens', 'lines', 'lines')
@default_score
def check(input_stream, output_stream, judge_stream, **kwargs):
    [t] = input_stream.read.int(lim.t)
    for cas in range(t):
        [n] = input_stream.read.int(lim.n)
        [a] = input_stream.read.ints(n, lim.a)
        cont_b = get_sequence(output_stream, exc=Wrong)
        judge_b = get_sequence(judge_stream, exc=Fail)
        check_valid(a, cont_b, exc=Wrong)
        check_valid(a, judge_b, exc=Fail)
        if len(cont_b) < len(judge_b): raise Wrong("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

if __name__ == '__main__': check_files(check, title="Split")
