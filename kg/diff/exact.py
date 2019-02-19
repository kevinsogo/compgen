from itertools import zip_longest
from kg.checkers import * ### @import

def is_exactly_equal(seq1, seq2):
    return all(val1 == val2 for val1, val2 in zip_longest(seq1, seq2))

@set_checker()
@default_score
def checker(input_file, output_file, judge_file, **kwargs):
    output_lines = list(output_file)
    judge_lines = list(judge_file)
    if not is_exactly_equal(output_lines, judge_lines):
        ### @@if format not in ('pg', 'hr') {
        if 'output_path' in kwargs and 'judge_path' in kwargs:
            import difflib
            diff = '\n'.join(difflib.unified_diff(output_lines, judge_lines, fromfile='Output File', tofile='Judge File'))

            N = 1111
            if len(diff) > N+3: diff = diff[:N] + '...'
            assert len(diff) <= N+3

            print('Incorrect. Diff:')
            print(diff)
        ### @@ }
        raise WA('Incorrect.')

if __name__ == '__main__': chk(help="Exact diff checker")
