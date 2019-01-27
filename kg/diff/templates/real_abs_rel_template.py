# Checks for an XXX error ### @replace "XXX", ('absolute/relative' if has_rel else 'absolute')
# with an error of at most 1e-XXX ### @replace "XXX", prec

# Don't edit this file. Edit real_abs_rel_template.py instead, and then run _real_check_gen.py
# Oh, actually, you're editing the correct file. Go on.                                          ### @if False

raise Exception("You're not supposed to run this!!!")                                            ### @if False
from itertools import zip_longest
from decimal import Decimal as D, InvalidOperation
from kg.checkers import * ### @keep @import

EPS = 0 ### @replace 0, "D('1e-{}')".format(prec)

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
                    err = error(D(v1), D(v2)) ### @replace "error", "abs_rel_error" if has_rel else "abs_error"
                except InvalidOperation:
                    raise WA("Unequal tokens that are not numbers: {} != {}".format(repr(v1), repr(v2)))
                worst = max(worst, err)
                if err > EPS:
                    print('Found an error of', worst) ### @keep @if format != 'hr'
                    raise WA("Bad precision.")
    print('Worst error:', worst) ### @keep @if format not in ('pg', 'hr')

help_ = ('Compare if two sequences of real numbers are "close enough" (by XXX). ' ### @replace 'XXX', '1e-' + str(prec)
    "Uses XXX error.") ### @replace 'XXX', 'absolute/relative' if has_rel else 'absolute'
if __name__ == '__main__': chk(help=help_)
