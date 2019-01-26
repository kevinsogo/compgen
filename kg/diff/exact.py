from itertools import zip_longest
from kg.checkers import * ### @import

def is_exactly_equal(seq1, seq2):
    return all(val1 == val2 for val1, val2 in zip_longest(seq1, seq2))

@set_checker()
@default_score
def checker(input_file, output_file, judge_file, **kwargs):
    if not is_exactly_equal(output_file, judge_file):
        ### @@if format not in ('pg', 'hr') {
        if 'output_path' in kwargs and 'judge_path' in kwargs:
            import subprocess
            from subprocess import PIPE

            p = subprocess.run(['diff', kwargs['output_path'], kwargs['judge_path']], stdout=PIPE, encoding='utf-8')

            to_print = p.stdout
            if len(to_print) > 111+3: to_print = to_print[:111] + '...'
            assert len(to_print) <= 111+3

            print('Incorrect. Diff:')
            print(to_print)
        ### @@ }
        raise WA('Incorrect.')

if __name__ == '__main__': chk(help="Exact diff checker")
