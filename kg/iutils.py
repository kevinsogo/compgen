import re
from sys import stdout
from string import digits
from itertools import islice




def set_handler(parser, default_file=stdout):
    def _set_handler(handler):
        parser.set_defaults(handler=handler, default_file=default_file)
        # return handler # Let's not return this, to ensure that they are not called.
    return _set_handler


inf = 10**18
r_int = r'0|(?:-?[1-9]\d*)'
r_sint = r'[+-](?:0|(?:[1-9]\d*))'

patterns = [
    r'(?P<start>{r_int})(?:(?:\.\.)|-)(?P<end>{r_int})\((?P<step>{r_sint})\)',
    r'(?P<start>{r_int})(?:(?:\.\.)|-)(?P<end>{r_int})',
    r'(?P<start>{r_int})\((?P<step>{r_sint})\)',
    r'(?P<start>{r_int})',
]

patterns = [re.compile(('^' + pat + '$').format(r_int=r_int, r_sint=r_sint)) for pat in patterns]

def t_range(s):
    for pat in patterns:
        m = pat.match(s)
        if m:
            m = m.groupdict()
            start = int(m['start'])
            step = int(m.get('step', 1))
            if 'end' in m:
                end = int(m['end'])
                if step < 0: end -= 1
                if step > 0: end += 1
            elif 'step' in m:
                if step < 0:
                    end = -inf
                elif step > 0:
                    end = +inf
                else:
                    end = None
            else:
                assert step == 1
                end = start + 1
            if step and end is not None and (end - start) * step >= 0:
                return range(start, end, step)
    raise ValueError("Range cannot be read: {}".format(repr(s)))

def t_sequence_ranges(s):
    return [t_range(p) for p in s.split(',')]

def t_sequence(s):
    for r in s.split(','):
        yield from r

# TODO make unit tests
# print(list(islice(t_sequence('2'), 100)))
# print(list(islice(t_sequence('12'), 100)))
# print(list(islice(t_sequence('-2'), 100)))
# print(list(islice(t_sequence('3,5-7,11'), 100)))
# print(list(islice(t_sequence('3,5-7,9..11'), 100)))
# print(list(islice(t_sequence('3,5-7,9..11,15(+1)'), 100)))
# print(list(islice(t_sequence('3,5-7,9..11,15(+2)'), 100)))
# print(list(islice(t_sequence('5(+2)'), 100)))
# print(list(islice(t_sequence('5..19(+2)'), 100)))
