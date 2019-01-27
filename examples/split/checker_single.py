from kg.checkers import * ### @import

@chk.get_one_input
def get_one_input(file, **kwargs):
    n = int(next(file))
    a = list(map(int, next(file).strip().split()))
    ensure(len(a) == n, "Invalid length in input", exc=Fail)
    return a

@chk.get_output_from_input
@chk.get_judge_data_from_input
def get_output_from_input(file, a, **kwargs):
    exc = kwargs['exc']
    try:
        m = int(next(file).rstrip())
        b = list(map(int, next(file).rstrip().split(' ')))
    except Exception as e:
        raise exc("Failed to get a sequence: " + str(e)) from e
    ensure(m >= 0, "Invalid length", exc=exc)
    ensure(len(b) == m, lambda: "Expected {} numbers but got {}".format(m, len(b)), exc=exc)
    return b

def check_valid(a, b, exc=Exception):
    # check subsequence
    j = 0
    for i in range(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=exc)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@set_single_checker(no_extra_chars=True)
def check_solution(a, cont_b, judge_b, **kwargs):
    check_valid(a, cont_b, exc=WA)
    check_valid(a, judge_b, exc=Fail) # remove for speed
    if len(cont_b) < len(judge_b): raise WA("Suboptimal solution")
    if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")
    return 1.0

if __name__ == '__main__': chk(title="Split")
