from kg.checkers import * ### @import

def is_subsequence(a, b):
    ... # code omitted

def get_sequence(stream, exc=Exception):
    [m] = stream.read.int().eoln
    [b] = stream.read.ints(m).eoln
    ensure(m >= 0, exc("Invalid length"))
    ensure(len(b) == m, exc(f"Expected {m} numbers but got {len(b)}"))
    return b

def check_valid(a, b, exc=Exception):
    ensure(is_subsequence(a, b), exc("Not a subsequence!"))
    ensure(len(b) == len(set(b)), exc("Values not unique!"))

@checker
def check(input_stream, output_stream, judge_stream, **kwargs):
    [z] = input_stream.read.int().eoln
    for cas in range(z):
        [n] = input_stream.read.int().eoln
        [a] = input_stream.read.ints(n).eoln
        cont_b = get_sequence(output_stream, exc=Wrong)
        judge_b = get_sequence(judge_stream, exc=Fail)
        check_valid(a, cont_b, exc=Wrong)
        check_valid(a, judge_b, exc=Fail)
        if len(cont_b) < len(judge_b): raise Wrong("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

    return 1.0

if __name__ == '__main__': check_files(check)
