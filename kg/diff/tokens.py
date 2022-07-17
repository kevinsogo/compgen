from itertools import zip_longest
from kg.checkers import * ### @import

def is_exactly_equal(seq1, seq2):
    return all(val1 == val2 for val1, val2 in zip_longest(seq1, seq2))

@checker('tokens', extra_chars_allowed=['input'])
@default_score
def check_tokens(input_file, output_file, judge_file, **kwargs):
    if not is_exactly_equal(output_file, judge_file):
        raise Wrong("Incorrect.")

if __name__ == '__main__': check_files(check_tokens, help="Compare if the sequence of tokens are the same.")
