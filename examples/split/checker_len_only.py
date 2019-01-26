from kg.checkers import * ### @import

@chk.get_one_input
def get_one_input(file, **kwargs):
    n = int(next(file))
    a = list(map(int, next(file).strip().split()))
    ensure(len(a) == n, "Invalid length in input", exc=Fail)
    return a

@chk.get_output_from_input
def get_output_from_input(file, a, **kwargs):
    try:
        m = int(next(file).rstrip())
        b = list(map(int, next(file).rstrip().split(' ')))
    except Exception as e:
        raise ParseError("Failed to get a sequence: " + str(e))
    ensure(m >= 0, "Invalid length", exc=WA)
    ensure(len(b) == m, lambda: "Expected {} numbers but got {}".format(m, len(b)), exc=WA)
    return b

@chk.get_judge_data_from_input
def get_judge_data_from_input(file, a, **kwargs):
    return int(next(file))

@set_multi_checker(no_extra_chars=True)
@default_return(1.0)
def check_solution(a, b, ans, **kwargs):
    # check subsequence
    j = 0
    for i in range(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=WA)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=WA)
    if len(b) < ans: raise WA("Suboptimal solution")
    if len(b) > ans: raise Fail("Judge data incorrect!")

if __name__ == '__main__': chk(title="Split")
