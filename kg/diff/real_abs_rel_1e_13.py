# Checks for an absolute/relative error 
# with an error of at most 1e-13 

# Don't edit this file. Edit real_abs_rel_template.py instead, and then run _real_check_gen.py

from itertools import zip_longest
from decimal import Decimal as D, InvalidOperation
from kg.checkers import * ### @import

EPS = D('1e-13') 

EPS *= 1+D('1e-5') # add some leniency
@set_checker()
@default_score
def checker(input_file, output_file, judge_file, **kwargs):
    worst = 0
    for line1, line2 in zip_longest(output_file, judge_file):
        if (line1 is None) != (line2 is None): raise WA("Unequal number of lines")
        p1 = line1.rstrip().split(" ")
        p2 = line2.rstrip().split(" ")
        if len(p1) != len(p2): raise WA("Incorrect number of values in line")
        for v1, v2 in zip(p1, p2):
            if v1 != v2: # they're different as tokens. try considering them as numbers
                try:
                    err = abs_rel_error(D(v1), D(v2)) 
                except InvalidOperation:
                    raise WA(f"Unequal tokens that are not numbers: {repr(v1)} != {repr(v2)}")
                worst = max(worst, err)
                if err > EPS:
                    print('Found an error of', worst) ### @if format != 'hr'
                    raise WA("Bad precision.")
    print('Worst error:', worst) ### @if format not in ('pg', 'hr')

help_ = ('Compare if two sequences of real numbers are "close enough" (by 1e-13). ' 
    "Uses absolute/relative error.") 
if __name__ == '__main__': chk(help=help_)
