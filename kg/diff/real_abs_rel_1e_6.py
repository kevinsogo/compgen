from itertools import zip_longest

from decimal import Decimal as D

from kg.checkers import * ### @import

def is_exactly_equal(seq1, seq2):
    return all(val1 == val2 for val1, val2 in zip_longest(seq1, seq2))
    for val1, val2 in zip_longest(seq1, seq2):
        if val1 != val2: return False
    return True

EPS = 1e-6*(1+1e-5)

@set_checker()
@default_score
def checker(input_file, output_file, judge_file, **kwargs):
    for line1, line2 in zip_longest(output_file, judge_file):
        p1 = line1.rstrip().split(" ")
        p2 = line2.rstrip().split(" ")
        if len(p1) != len(p2): raise WA("Incorrect number of values in line")
        for v1, v2 in zip(p1, p2):
            print(abs_rel_error(D(v1), D(v2)))
            if abs_rel_error(D(v1), D(v2)) > EPS:
                raise WA("Bad precision.")

if __name__ == '__main__': chk(help="Compare if the sequence of tokens are the same.")
