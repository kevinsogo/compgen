from itertools import zip_longest
from kg.checkers import * ### @import

def is_exactly_equal(seq1, seq2):
    return all(val1 == val2 for val1, val2 in zip_longest(seq1, seq2))

@set_checker("tokens")
@default_score
def checker(input_file, output_file, judge_file, **kwargs):
    if not is_exactly_equal(output_file, judge_file):
        raise Wrong("Incorrect.")

if __name__ == '__main__': chk(help="Compare if the sequence of tokens are the same.")
