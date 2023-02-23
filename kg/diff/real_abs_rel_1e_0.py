# Checks for an absolute/relative error 
# with an error of at most 1e-0 

# Don't edit this file. Edit real_abs_rel_template.py instead, and then run _real_check_gen.py

from itertools import zip_longest
from decimal import Decimal, InvalidOperation
from kg.checkers import * ### @import

EPS = Decimal('1e-0') 

EPS *= 1+Decimal('1e-5') # add some leniency
@checker(extra_chars_allowed=['input'])
@default_score
def check_real(input_file, output_file, judge_file, **kwargs):
    worst = 0
    try:
        for line1, line2 in zip_longest(output_file, judge_file):
            if (line1 is None) != (line2 is None): raise Wrong("Unequal number of lines")
            p1 = line1.rstrip().split(" ")
            p2 = line2.rstrip().split(" ")
            if len(p1) != len(p2): raise Wrong("Incorrect number of values in line")
            for v1, v2 in zip(p1, p2):
                if v1 != v2:
                    try:
                        v1, v2 = Decimal(v1), Decimal(v2)
                    except InvalidOperation as ex:
                        raise Wrong(f"Unequal tokens that are not numbers: {v1!r} != {v2!r}") from ex
                    else:
                        err = abs_rel_error(v1, v2) 
                        worst = max(worst, err)
                        if err > EPS:
                            raise Wrong(f"Not within the required precision: got error {err}")
    finally:
        ...
        print('Worst error found:', worst) ### @if format not in ('pg', 'hr', 'cms')

if __name__ == '__main__':
    check_files(check_real,
        help='Compare if two sequences of real numbers are "close enough" (by 1e-0). ' 
             'Uses absolute/relative error.' 
    )
