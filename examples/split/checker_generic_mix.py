from kg.checkers import * ### @import

def get_sequence(file, exc=Exception):
    try:
        m = int(next(file).rstrip())
        b = list(map(int, next(file).rstrip().split(' ')))
    except Exception as e:
        raise ParseError("Failed to get a sequence") from e
    ensure(m >= 0, "Invalid length", exc=exc)
    ensure(len(b) == m, lambda: exc(f"Expected {m} numbers but got {len(b)}"))
    return b

def check_valid(a, b, exc=Exception):
    # check subsequence
    j = 0
    for i in range(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=exc)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@set_checker('tokens', 'lines', 'lines', no_extra_chars=True)
@default_score
def check_solution(input_file, output_file, judge_file, **kwargs):
    z = int(next(input_file))
    for cas in range(z):
        n = int(next(input_file))
        ensure(n >= 1, "Judge data invalid!", exc=Fail)
        a = [int(next(input_file)) for i in range(n)]
        cont_b = get_sequence(output_file, exc=Wrong)
        judge_b = get_sequence(judge_file, exc=Fail)
        check_valid(a, cont_b, exc=Wrong)
        check_valid(a, judge_b, exc=Fail)
        if len(cont_b) < len(judge_b): raise Wrong("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

if __name__ == '__main__': chk("Split")
