from kg.checkers import * ### @import

def is_subsequence(a, b):
    ... # code omitted

def get_sequence(file, exc=Exception):
    try:
        m = int(next(file).rstrip())
        b = list(map(int, next(file).rstrip().split(' ')))
    except Exception as e:
        raise ParseError("Failed to get a sequence") from e
    ensure(m >= 0, exc("Invalid length"))
    ensure(len(b) == m, exc(f"Expected {m} numbers but got {len(b)}"))
    return b

def check_valid(a, b, exc=Exception):
    ensure(is_subsequence(a, b), exc("Not a subsequence!"))
    ensure(len(b) == len(set(b)), exc("Values not unique!"))

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    z = int(next(input_file))
    for cas in range(z):
        n = int(next(input_file))
        a = list(map(int, next(input_file).strip().split()))
        if len(a) != n: raise Fail("Judge input invalid")
        cont_b = get_sequence(output_file, exc=Wrong)
        judge_b = get_sequence(judge_file, exc=Fail)
        check_valid(a, cont_b, exc=Wrong)
        check_valid(a, judge_b, exc=Fail)
        if len(cont_b) < len(judge_b): raise Wrong("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

    if output_file.has_next(): raise Wrong("Extra characters at the end of the output file")
    if judge_file.has_next(): raise Fail("Extra characters at the end of the judge file!")
    return 1.0

if __name__ == '__main__': chk()
