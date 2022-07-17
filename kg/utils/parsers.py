import collections, decimal, re, string

from .utils import * ### @import
from .intervals import * ### @import

class ParsingError(Exception): ...

def strict_check_range(x, *args, type="Number"):
    if len(args) == 2:
        l, r = args
        if not (l <= x <= r):
            raise ParsingError(f"{type} {x} not in [{l}, {r}]")
    elif len(args) == 1:
        r, = args
        if isinstance(r, Intervals):
            if x not in r:
                raise ParsingError(f"{type} {x} not in {r}")
        else:
            if not (0 <= x < r):
                raise ParsingError(f"{type} {x} not in [0, {r})")
    elif len(args) == 0:
        pass
    else:
        raise ParsingError(f"Invalid arguments for range check: {args}")
    return x


_int_re = re.compile(r'^(?:0|-?[1-9]\d*)\Z')
intchars = {'-', *string.digits}
def strict_int(x, *args, as_str=False, validate=True): ### @@ if False {
    ''' Check if the string x is a valid integer token, and that it satisfies certain constraints.

    as_str: if True, return the string as is, rather than parsing. (default False)

    Sample usage:
    strict_int(x) # just checks if the token is a valid integer.
    strict_int(x, 5) # checks if x is in the half-open interval [0, 5)
    strict_int(x, 5, 8) # checks if x is in the closed interval [5, 8]
    strict_int(x, intervals) # check if  is in the 'intervals' Intervals
    '''
    ### @@ }
    
    # validate
    if validate:
        if not _int_re.fullmatch(x):
            raise ParsingError(f"Expected integer literal, got {x!r}")
    
    # allow to return as string
    if [*args] == ['str']:
        warn("passing 'str' is deprecated. Use as_str=True instead.") ### @if False
        as_str = True
        args = []
    if as_str:
        if args: raise ParsingError("Additional arguments not allowed if as_str is True")
        return x
    
    # parse and check range
    try:
        x = int(x)
    except ValueError as ex:
        raise ParsingError(f"Cannot parse {overflow_ell(x)!r} to int") from ex
    strict_check_range(x, *args, type="Integer")
    return x


_real_re = re.compile(r'^(?P<sign>[+-]?)(?P<int>0?|(?:[1-9]\d*))(?:(?P<dot>\.)(?P<frac>\d*))?\Z')
realchars = intchars | {'+', '-', '.'}

_StrictRealData = collections.namedtuple('_StrictRealData', ['sign', 'dot', 'neg_zero', 'dot_lead', 'dot_trail', 'places'])
def _strict_real_data(x):
    match = _real_re.fullmatch(x)
    if match is None: return None

    sign, int_, dot, frac = map(match.group, ('sign', 'int', 'dot', 'frac'))

    # must have at least one digit
    if not (int_ or frac): return None

    return _StrictRealData(sign=sign, dot=dot,
        neg_zero=sign == '-' and not int_.strip('0') and not frac.strip('0'),
        dot_lead=dot and not int_,
        dot_trail=dot and not frac,
        places=len(frac) if frac else 0,
    )


def strict_real(x, *args, as_str=False, max_places=None, places=None, require_dot=False, allow_plus=False,
        allow_neg_zero=False, allow_dot_lead=False, allow_dot_trail=False, validate=True): ### @@ if False {
    '''Check if the string x is a valid real token, and that it satisfies certain constraints.

    It receives the same arguments as strict_int, and also receives the following in addition:

    places: If it is an integer, then x must have exactly 'places' after the decimal point.
    as_str: if True, return the string as is, rather than parsing. (default False)
    require_dot: If True, then the '.' character has to appear. (default False)
    allow_plus: If True, then the '+' sign is allowed. (default False)
    allow_neg_zero: If True, then "negative zero", like, -0.0000, is allowed. (default False)
    allow_dot_lead: If True, then a leading dot, like, ".420", is allowed. (default False)
    allow_dot_trail: If True, then a trailing dot, like, "420.", is allowed. (default False)
    '''
    ### @@ }

    # validate
    if validate:
        data = _strict_real_data(x)
        if not data:
            raise ParsingError(f"Expected real literal, got {x!r}")
        if require_dot and not data.dot:
            raise ParsingError(f"Dot required, got {x!r}")
        if not allow_plus and data.sign == '+':
            raise ParsingError(f"Plus sign not allowed, got {x!r}")
        if not allow_neg_zero and data.neg_zero:
            raise ParsingError(f"Real negative zero not allowed, got {x!r}")
        if not allow_dot_lead and data.dot_lead:
            raise ParsingError(f"Real with leading dot not allowed, got {x!r}")
        if not allow_dot_trail and data.dot_trail:
            raise ParsingError(f"Real with trailing dot not allowed, got {x!r}")
        if max_places is not None and data.places > max_places:
            raise ParsingError(f"Decimal place count of {x!r} (={data.places}) exceeds {max_places}")
        if places is not None:
            if isinstance(places, Intervals):
                if data.places not in places:
                    raise ParsingError(f"Decimal place count of {x!r} (={data.places}) not in {places}")
            else:
                if data.places != places:
                    raise ParsingError(f"Decimal place count of {x!r} (={data.places}) not equal to {places}")

    # allow to return as string
    if [*args] == ['str']:
        warn("passing 'str' is deprecated. Use as_str=True instead.") ### @if False
        as_str = True
        args = []
    if as_str:
        if args: raise ParsingError("Additional arguments not allowed if as_str is True")
        return x

    # parse and validate
    try:
        x = decimal.Decimal(x)
    except ValueError as ex:
        raise ParsingError(f"Cannot parse {overflow_ell(x)!r} to Decimal") from ex
    strict_check_range(x, *args, type="Real")
    return x
