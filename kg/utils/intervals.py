import collections, enum, functools, itertools, operator

from .utils import * ### @import

# values represent sorting priority
class BType(enum.IntEnum):
    UE = -3  # upper bound, exclusive
    LI = -1  # lower bound, inclusive
    UI = +1  # upper bound, inclusive
    LE = +3  # lower bound, exclusive

B_BRACKETS = {
    BType.UE: ')',
    BType.LI: '[',
    BType.UI: ']',
    BType.LE: '(',
}
BTYPE_FOR_BRACKET = {bracket: btype for btype, bracket in B_BRACKETS.items()}

B_FLIPS = {
    BType.UE: BType.LI,
    BType.LI: BType.UE,
    BType.UI: BType.LE,
    BType.LE: BType.UI,
}

B_NEGS = {
    BType.UE: BType.LE,
    BType.LE: BType.UE,
    BType.UI: BType.LI,
    BType.LI: BType.UI,
}

LO_BTYPES = {BType.LE, BType.LI}
UP_BTYPES = {BType.UE, BType.UI}
LO_BOUND = (-float('inf'), BType.LI) # [-inf
UP_BOUND = (+float('inf'), BType.UI) # +inf]

# TODO check if __and__ or a classmethod or a classmethod can be cached
@functools.lru_cache(maxsize=500)
def _intersect_intervals(a, b):
    def ibounds(a, b):
        ia = ib = 0
        while ia < len(a) and ib < len(b):
            lo = max(a[ia], b[ib])
            up = min(a[ia + 1], b[ib + 1])
            if lo < up:
                yield lo
                yield up
            if up == a[ia + 1]: ia += 2
            if up == b[ib + 1]: ib += 2

    return Intervals(ibounds(a._bds, b._bds))


class Intervals(collections.Hashable): ### @@ if False {
    """Immutable collection of disjoint nonempty intervals.

    Each interval can have inclusive/exclusive lower/upper bounds.

    Assumes the bounds and values used are:

    - in total order,
    - comparable to -inf and +inf, and
    - all in [-inf, +inf]

    where inf := float('inf')
    """
    ### @@ }

    __slots__ = '_bds', '_hash', '_complement'

    def __init__(self, bounds, *, _complement=None):
        self._bds = []
        for bound in bounds:
            if self._bds and self._bds[-1] >= bound:
                raise ValueError("The bounds must be sorted")
            if len(self._bds) % 2 == 0:
                if not Intervals.is_lower(*bound): raise ValueError("At least one of the lower bounds is invalid")
                self._bds.append(bound)
            else:
                if not Intervals.is_upper(*bound): raise ValueError("At least one of the upper bounds is invalid")

                if len(self._bds) > 2 and Intervals.adjacent(*self._bds[-2], *self._bds[-1]):
                    self._bds[-2:] = [bound]
                else:
                    self._bds.append(bound)

        if len(self._bds) % 2:
            raise ValueError("There must be an even number of arguments")
        if self._bds and not (LO_BOUND <= self._bds[0] and self._bds[-1] <= UP_BOUND):
            raise ValueError("The intervals must be a subset of [-inf, +inf]")
        self._hash = None
        self._complement = _complement
        super().__init__()

    def __hash__(self):
        if self._hash is None:
            self._bds = tuple(self._bds)
            self._hash = hash(self._bds) ^ (0xC0FFEE << 3)
        return self._hash

    def __eq__(self, other):
        # the 'hash' here is to turn _bounds into a tuple
        return hash(self) == hash(other) and self._bds == other._bds

    def __ne__(self, other):
        return not (self == other)

    def __contains__(self, value):

        if not self._bds:
            return False
        if not Intervals.satisfies(value, *self._bds[0]):
            return False
        if not Intervals.satisfies(value, *self._bds[-1]):
            return False

        # binary search to find the interval containing it
        l, r = 0, len(self._bds)
        while r - l > 2:
            m = l + r >> 2 << 1 # must be even
            if Intervals.satisfies(value, *self._bds[m]):
                l = m
            elif Intervals.satisfies(value, *self._bds[m - 1]):
                r = m
            else:
                # it falls in between intervals
                return False

        assert r - l == 2 ### @if False
        return True

    def __and__(self, other):
        """intersection of sets"""
        # return ~(~self | ~other)  # if implementing __or__ manually is faster
        if hash(self) > hash(other): return other & self
        return _intersect_intervals(self, other)

    def __or__(self, other):
        """union of sets"""
        return ~(~self & ~other)

    def __xor__(self, other):
        """symmetric difference of sets"""
        return (~self & other) | (self & ~other)

    def __invert__(self):
        """complement of set relative to [-inf, +inf]"""
        if self._complement is None:
            def cbounds(b):
                loi = bool(b and b[0]  == LO_BOUND)
                upi = bool(b and b[-1] == UP_BOUND)
                if not loi: yield LO_BOUND
                for i in range(loi, len(b) - upi):
                    yield Intervals.flip(*b[i])
                if not upi: yield UP_BOUND
            self._complement = Intervals(cbounds(self._bds), _complement=self)
        return self._complement

    @staticmethod
    def is_lower(bound, btype): return btype in LO_BTYPES

    @staticmethod
    def is_upper(bound, btype): return btype in UP_BTYPES

    @staticmethod
    def satisfies(value, bound, btype):
        # TODO use 'match'
        if btype == BType.UE: return value < bound
        if btype == BType.LI: return bound <= value
        if btype == BType.UI: return value <= bound
        if btype == BType.LE: return bound < value
        assert False #

    @staticmethod
    def adjacent(bound1, btype1, bound2, btype2):
        return bound1 == bound2 and btype2.value - btype1.value == 2

    @staticmethod
    def flip(bound, btype):
        return bound, B_FLIPS[btype]

    def _pieces(self):
        return ((self._bds[i], self._bds[i + 1]) for i in range(0, len(self._bds), 2))

    def __abs__(self):
        return (self & B_NONNEG_INTERVAL) | (-self & B_NONPOS_INTERVAL)

    def __neg__(self):
        return Intervals((-bound, B_NEGS[btype]) for bound, btype in reversed(self._bds))

    def __bool__(self):
        return bool(self._bds)

    def __str__(self):
        return " | ".join(
            f"{B_BRACKETS[ltyp]}{lbound}, {rbound}{B_BRACKETS[rtyp]}"
            for (lbound, ltyp), (rbound, rtyp) in self._pieces()
        ) if self else "<empty set>"

    def __repr__(self):
        return f"{self.__class__.__name__}({tuple(self._bds)!r})"

    @classmethod
    def from_tokens(cls, *tokens):
        if len(tokens) % 4 != 0: raise ValueError("The number of tokens must be a multiple of 4")
        def bounds():
            for i in range(0, len(tokens), 4):
                lch, lvl, uvl, uch = tokens[i:i+4]
                yield lvl, BTYPE_FOR_BRACKET[lch]
                yield uvl, BTYPE_FOR_BRACKET[uch]
        return cls(bounds())

    @property
    def lower_bound(self): return self._bds[0][0]  if self._bds else +float('inf')

    @property
    def upper_bound(self): return self._bds[-1][0] if self._bds else -float('inf')



B_FULL_INTERVAL = Intervals([LO_BOUND, UP_BOUND])
B_NONNEG_INTERVAL = Intervals([(0, BType.LI), UP_BOUND])
B_NONPOS_INTERVAL = Intervals([LO_BOUND, (0, BType.UI)])




class VarMeta(type):
    def __pos__(self): return self()
    def __abs__(self): return abs(self())
    def __neg__(self): return -self()

class Var(metaclass=VarMeta):

    __slots__ = 'intervals', '_bd_ct', '_app_pref', '_app'

    def __init__(self, intervals=B_FULL_INTERVAL, *, _bd_ct=0, _app_pref='', _app=()):
        if not isinstance(intervals, Intervals):
            raise TypeError("The first argument must be an Intervals instance")
        self.intervals = intervals
        self._bd_ct = _bd_ct
        self._app_pref = _app_pref
        self._app = tuple(_app)
        super().__init__()

    def _add_bound(self):
        if self._bd_ct >= 2:
            raise RuntimeError("Cannot bound this Var anymore")
        self._bd_ct += 1

    def _add(self, intervals):
        for app in self._app: intervals = app(intervals)
        self.intervals &= intervals
        self._add_bound()
        return self

    def __le__(self, v): return self._add(Intervals([LO_BOUND, (v, BType.UI)]))
    def __lt__(self, v): return self._add(Intervals([LO_BOUND, (v, BType.UE)]))
    def __ge__(self, v): return self._add(Intervals([(v, BType.LI), UP_BOUND]))
    def __gt__(self, v): return self._add(Intervals([(v, BType.LE), UP_BOUND]))
    def __eq__(self, v): return self._add(Intervals([(v, BType.LI), (v, BType.UI)]))
    def __ne__(self, v): return self._add(~Intervals([(v, BType.LI), (v, BType.UI)]))

    def __pos__(self):
        if self._bd_ct: raise TypeError("Cannot get pos if already bounded")
        return self

    def __abs__(self):
        if self._bd_ct: raise TypeError("Cannot get abs if already bounded")
        return Var(self.intervals,
            _app_pref=f"abs {self._app_pref}",
            _app=(Intervals.__abs__, *self._app),
        )

    def __neg__(self):
        if self._bd_ct: raise TypeError("Cannot get neg if already bounded")
        return Var(self.intervals,
            _app_pref=f"neg {self._app_pref}",
            _app=(Intervals.__neg__, *self._app),
        )

    def _combin(self, op, other):
        if isinstance(other, Var): other = other.intervals
        if not isinstance(other, Intervals): return NotImplemented
        return Var(op(self.intervals, other), _bd_ct=2)

    def __and__(self, other): return self._combin(operator.and_, other)
    def __or__ (self, other): return self._combin(operator.or_,  other)
    def __xor__(self, other): return self._combin(operator.xor,  other)

    __rand__ = __and__
    __ror__  = __or__
    __rxor__ = __xor__

    def __str__(self):
        _app_pref = f'{self._app_pref}: ' if self._app_pref else ''
        return f"<{_app_pref}{self.intervals}>"

    __repr__ = __str__



# TODO remove 'Interval' (backwards incompatible) ### @if False
def interval(l, r): return l <= +Var <= r
Interval = interval = warn_on_call("'interval' deprecated; use a <= +Var <= b instead")(interval)

class Bounds(collections.Mapping):
    def __init__(self, bounds=None, **kwbounds):
        if isinstance(bounds, Bounds):
            bounds = bounds._attrs
        self._attrs = {}
        self.accessed = set() # keep track of which attrs were accessed, for validation info purposes.
        for name, value in itertools.chain((bounds or {}).items(), kwbounds.items()):
            if name.startswith('_'):
                raise ValueError("Variable names passed to Bounds cannot start with an underscore")
            if isinstance(value, Var): value = value.intervals  # freeze the Var
            if name in self._attrs:
                raise ValueError("Duplicate names for Bounds not allowed; use '&' instead to combine bounds")
            self._attrs[name] = value
        super().__init__()

    def __and__(self, other): ### @@ if False {
        ''' Combine two Bounds objects together. Merges intervals for conflicting attributes.
        If not both are intervals, an error is raised. '''
        ### @@ }
        combined = {}
        for attr in sorted(set(self._attrs) | set(other._attrs)):
            def combine(a, b):
                if a is None: return b
                if b is None: return a
                if isinstance(a, Intervals) and isinstance(b, Intervals): return a & b
                if not isinstance(a, Intervals) and not isinstance(b, Intervals): return b
                raise TypeError(f"Conflict for attribute {attr} in merging! {type(a)} vs {type(b)}")
            combined[attr] = combine(self._attrs.get(attr), other._attrs.get(attr))
        return Bounds(combined)

    def __len__(self):  return len(self._attrs)
    def __iter__(self): return iter(self._attrs)

    def __getitem__(self, name):
        if name not in self._attrs: raise KeyError(f"{name} not among the Bounds: {overflow_ell(', '.join(self._attrs))}")
        return getattr(self, name)

    def __getattr__(self, name):
        if name in self._attrs:
            self.accessed.add(name)
            value = self._attrs[name]
            setattr(self, name, value)
            return value
        raise AttributeError

    def __repr__(self): return f'{self.__class__.__name__}({self._attrs!r})'

    def __str__(self): return '{{Bounds:\n{}}}'.format(''.join(f'\t{attr}: {val}\n' for attr, val in self._attrs.items()))





### @@if False {
def test_some_stuff():
    

    # def L(ch, vl):
    #     assert m[ch] in LO_BTYPES
    #     return vl, m[ch]
    # def U(vl, ch):
    #     assert m[ch] in UP_BTYPES
    #     return vl, m[ch]

    # def I(*vals):
    #     assert len(vals) % 4 == 0
    #     vals = [*zip(vals[::2], vals[1::2])]
    #     vals = [*zip(vals[::2], vals[1::2])]
    #     vals = ((L(*p), U(*q)) for p, q in vals)
    #     return Intervals(val for pair in vals for val in pair)

    I = Intervals.from_tokens

    i1 = I('(', 10, 20, ']')
    i2 = I('[', -float('inf'), -100, ']', '[', 15, 25, ')', '(', 25, 30, ')', '[', 30, 31, ']', '(', 35, 40, ')', '[', 41, 41, ']', '(', 42, float('inf'), ']')
    print(i1)
    print(i2)
    print(~i1)
    print(~i2)
    print(i1 & i2)
    print(i1 | i2)
    print(i1 ^ i2)

    Op = collections.namedtuple('Op', ['type', 'make'])
    indiv_ops = [
        Op(type=BType.UE, make=(lambda b: (Intervals([LO_BOUND, (b, BType.UE)]), f'<{b}', (lambda v: v < b)))),
        Op(type=BType.LI, make=(lambda b: (Intervals([(b, BType.LI), UP_BOUND]), f'{b}<=', (lambda v: b <= v)))),
        Op(type=BType.UI, make=(lambda b: (Intervals([LO_BOUND, (b, BType.UI)]), f'<={b}', (lambda v: v <= b)))),
        Op(type=BType.LE, make=(lambda b: (Intervals([(b, BType.LE), UP_BOUND]), f'{b}<', (lambda v: b < v)))),
    ]
    pair_ops = [
        Op(type='and', make=(lambda i1, e1, c1, i2, e2, c2: ((i1 & i2), f'({e1} & {e2})', (lambda v: c1(v) and c2(v))))),
        Op(type='or',  make=(lambda i1, e1, c1, i2, e2, c2: ((i1 | i2), f'({e1} | {e2})', (lambda v: c1(v) or c2(v))))),
        Op(type='xor', make=(lambda i1, e1, c1, i2, e2, c2: ((i1 ^ i2), f'({e1} ^ {e2})', (lambda v: c1(v) ^ c2(v))))),
    ]

    def make_expression(rand, vs, n, eprob, iprob, nprob):
        if n == 0:
            if rand.random() < eprob:
                if rand.randrange(2):
                    return Intervals([LO_BOUND, UP_BOUND]), '⊤', lambda v: True
                else:
                    return Intervals([]), '⊥', lambda v: False
            else:
                infty = rand.random() < iprob
                while True:
                    b, ops = rand.choice([
                            (-float('inf'), [op for op in indiv_ops if op.type != BType.UE]),
                            (+float('inf'), [op for op in indiv_ops if op.type != BType.LE]),
                        ]) if infty else (rand.choice(vs), indiv_ops)
                    return rand.choice(ops).make(b)
        elif rand.random() < nprob:
            interv, ex, check = make_expression(rand, vs, n-1, eprob, iprob, nprob)
            return ~interv, f'~({ex})', lambda v, check=check: not check(v)
        else:
            l = rand.randrange(n)
            r = n - 1 - l
            lres = make_expression(rand, vs, l, eprob, iprob, nprob)
            rres = make_expression(rand, vs, r, eprob, iprob, nprob)
            return rand.choice(pair_ops).make(*lres, *rres)


    from kg.generators import KGRandom
    rand = KGRandom(11)

    z = 11111111
    for cas in range(z):
        n = rand.randint(1, rand.choice([3, 5, 7, 9, 11, 15, 21]))
        V = rand.randint(1, rand.choice([5, 11, 21, 51]))
        vals = range(-V, V+1)
        vals = sorted(rand.sample(vals, rand.randint(1, len(vals))))
        sc = 1 if rand.random() < 0.8 else rand.uniform(0.5, 1.5)
        vals = [v * sc for v in vals]
        eprob = rand.random() if rand.random() < 0.1 else rand.uniform(0, 0.1)
        iprob = rand.random() if rand.random() < 0.1 else rand.uniform(0, 0.1)
        nprob = rand.random() if rand.random() < 0.1 else rand.uniform(0, 0.1)
        interv, ex, check = make_expression(rand, vals, n, eprob, iprob, nprob)
        assert isinstance(interv, Intervals)
        qvals = {-float('inf'), float('inf'), *vals}
        vvals = [vals[0] - 10, *vals, vals[-1] + 10]
        for v1, v2 in zip(vvals, vvals[1:]):
            assert v1 < v2, (v1, v2)
            qvals.add((v1 + v2)/2)
            qvals.add(rand.uniform(v1, v2))

        print(f"Case {cas} of {z}: n={n} V={V} sc={sc} vals={vals} interv={interv}")
        print(ex)
        for v in qvals:
            assert check(v) == (v in interv)

        if rand.random() < 0.01:
            _intersect_intervals.cache_clear()


if __name__ == '__main__':
    test_some_stuff()
### @@}
