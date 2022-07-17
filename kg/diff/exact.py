from itertools import zip_longest
from kg.checkers import * ### @import

def is_exactly_equal(seq1, seq2):
    return all(val1 == val2 for val1, val2 in zip_longest(seq1, seq2))

@checker(extra_chars_allowed=['input'])
@default_score
def check_exactly_equal(input_file, output_file, judge_file, **kwargs):
    output_lines = list(output_file)
    judge_lines = list(judge_file)
    if not is_exactly_equal(output_lines, judge_lines):
        ### @@if format not in ('pg', 'hr', 'cms') {
        if 'output_path' in kwargs and 'judge_path' in kwargs:
            import difflib
            diff = '\n'.join(difflib.unified_diff(
                output_lines,
                judge_lines,
                fromfile='Output File',
                tofile='Judge File',
            ))

            N = 1111
            if len(diff) > N+3: diff = diff[:N] + '...'
            assert len(diff) <= N+3

            print('Incorrect. Diff:')
            print(diff)
        ### @@ }
        raise Wrong('Incorrect.')

if __name__ == '__main__': check_files(check_exactly_equal, help="Exact diff checker")
