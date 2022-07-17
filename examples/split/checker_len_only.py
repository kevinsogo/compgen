from kg.checkers import * ### @import

@checker.set
def get_one_input(stream, **kwargs):
    [n] = stream.read.int().eoln
    [a] = stream.read.ints(n).eoln
    return a

@checker.set
def get_output_for_input(stream, a, **kwargs):
    [m] = stream.read.int().eoln
    [b] = stream.read.ints(m).eoln
    return b

@checker.set
def get_judge_data_for_input(stream, a, **kwargs):
    [n] = stream.read.int().eoln
    return n

@checker.set
@default_return(1.0)
def check_one(a, b, ans, **kwargs):
    # check subsequence
    j = 0
    for i in range(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=Wrong)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=Wrong)
    if len(b) < ans: raise Wrong("Suboptimal solution")
    if len(b) > ans: raise Fail("Judge data incorrect!")


check = checker.make('lines')

if __name__ == '__main__': check_files(check, title="Split")
