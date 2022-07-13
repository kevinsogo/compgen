# Checks for an absolute error 
# with an error of at most 1e-11 

# Don't edit this file. Edit real_abs_rel_template.py instead, and then run _real_check_gen.py

from itertools import zip_longest
from decimal import Decimal, InvalidOperation
from kg.checkers import * ### @import

EPS = Decimal('1e-11') 

EPS *= 1+Decimal('1e-5') # add some leniency
@set_checker()
@default_score
def checker(input_file, output_file, judge_file, **kwargs):
    worst = 0
    for line1, line2 in zip_longest(output_file, judge_file):
        if (line1 is None) != (line2 is None): raise Wrong("Unequal number of lines")
        p1 = line1.rstrip().split(" ")
        p2 = line2.rstrip().split(" ")
        if len(p1) != len(p2): raise Wrong("Incorrect number of values in line")
        for v1, v2 in zip(p1, p2):
            if v1 != v2: # they're different as tokens. try considering them as numbers
                try:
                    err = abs_error(Decimal(v1), Decimal(v2)) 
                except InvalidOperation:
                    raise Wrong(f"Unequal tokens that are not numbers: {v1!r} != {v2!r}")
                worst = max(worst, err)
                if err > EPS:
                    print('Found an error of', worst) ### @if format not in ('hr', 'cms')
                    raise Wrong("Bad precision.")
    print('Worst error:', worst) ### @if format not in ('pg', 'hr', 'cms')

help_ = ('Compare if two sequences of real numbers are "close enough" (by 1e-11). ' 
    "Uses absolute error.") 
if __name__ == '__main__': chk(help=help_)
