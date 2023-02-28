"""Stuff related to primes.

This includes the Miller-rabin primality test, with a version valid for all 64-bit unsigned integers (hopefully no bugs!).
Can be wrong in principle for larger numbers, though the probability is very low.
"""

import itertools, math, random

class MathError(Exception): ...

def prime_sieve(n):
    sieve_is_prime = [False]*2 + [True]*(n-1)
    for i in range(2, n+1):
        if sieve_is_prime[i]:
            for j in range(i*i, n+1, i):
                sieve_is_prime[j] = False
    return sieve_is_prime

def get_primes(n, sieve_is_prime=None):
    if sieve_is_prime is None: sieve_is_prime = prime_sieve(n)
    return [p for p in range(n+1) if sieve_is_prime[p]]

_siv_isp = []
_siv_ps = []
def _set_sieve(n):
    _siv_isp[:] = prime_sieve(n)
    _siv_ps[:] = get_primes(n, _siv_isp)

_small_ps = []
def _set_small(s):
    _small_ps[:] = get_primes(s, _siv_isp)

_set_sieve(10**5)
_set_small(80)

def _check_composite(n, s, d, a):
    ''' check compositeness of n with witness a. (n,s,d) should satisfy d*2^s = n-1 and d is odd ''' ### @rem
    a %= n
    if a == 0: return False
    x = pow(a, d, n)
    if x == 1 or x == n - 1: return False
    for y in range(1, s):
        x = x * x % n
        if x == 1:     return True
        if x == n - 1: return False
    return True

# witnesses for different bounds (taken from http://miller-rabin.appspot.com/ )
_witnesses_bounds = [
    (341531,             [9345883071009581737]),
    (716169301,          [336781006125, 9639812373923155]),
    (350269456337,       [4230279247111683200, 14694767155120705706, 16641139526367750375]),
    (55245642489451,     [2, 141889084524735, 1199124725622454117, 11096072698276303650]),
    (7999252175582851,   [2, 4130806001517, 149795463772692060, 186635894390467037, 3967304179347715805]),
    (585226005592931977, [2, 123635709730000, 9233062284813009, 43835965440333360, 761179012939631437, 1263739024124850375]),
]
# set of witnesses for < 2^64 (taken from http://miller-rabin.appspot.com/ )
_i64_witnesses = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]

def is_prime_miller_rabin(n, *, more_witnesses=()): ### @@rem {
    """
    returns True if n is probably prime, and False if n is definitely not prime.
    if n < 2^64, then is_prime(n) never returns a wrong answer. (hopefully!)
    """
    ### @@}
    if n < 2: return False
    # if too small, check _siv_isp   ### @rem
    if n < len(_siv_isp): return _siv_isp[n]
    # check divisibility with small primes   ### @rem
    if any(n % p == 0 for p in _small_ps): return False
    # find (d,s) such that d*2^s = n-1 with d odd   ### @rem
    d, s = n - 1, 0
    while not d & 1: d >>= 1; s += 1
    # find the best set of witnesses   ### @rem
    for bound, bound_ws in _witnesses_bounds:
        if n < bound:
            best_witnesses = bound_ws
            break
    else:
        best_witnesses = _i64_witnesses
    # check compositeness with the witnesses   ### @rem
    for a in itertools.chain(best_witnesses, more_witnesses):
        if _check_composite(n, s, d, a): return False
    return True

def is_prime_naive(n):
    if n < 2: return False
    if n < len(_siv_isp): return _siv_isp[n]
    for p in _siv_ps:
        if p * p > n: break
        if n % p == 0: return False
    while p * p <= n:
        if n % p == 0: return False
        p += 1
    return True

### @@ rem {
# TODO implement some O(n^(1/3)) primality test/factorization (perhaps Fermat+Lehman?) or something,
# O(n^(1/4)) also possible [SQUFOF algorithm] but may be too hard to implement and verify
### @@ }

# 'guarantee' is deprecated ### @rem
def is_prime(n, *, guarantee=True):
    return is_prime_miller_rabin(n, more_witnesses=(random.randint(2, n-2) for i in range(min(16, int(math.log(n)/4)) if n >= 2**64 else 0)))

def next_prime(n, *, guarantee=True):
    while not is_prime(n): n += 1
    return n

def prev_prime(n, *, guarantee=True):
    if n < 2: raise MathError(f"There is no prime <= {n}")
    while not is_prime(n): n -= 1
    assert n >= 2
    return n

### @@ rem {
def test_some_stuff():
    import random
    rand = random.Random(11)
    def test_on(N, *, NN=10**5*3):
        gps = get_primes(N)
        print("sieve 1 up to", N, "done", len(gps))
        isps = prime_sieve(N)
        print("sieve 2 up to", N, "done", sum(isps))
        sgps = {*gps}
        assert sorted(sgps) == gps
        assert len(isps) == N + 1
        print("set + sort done", len(sgps))
        for n in range(-100, N+1):
            isp = is_prime(n)
            assert isp == (n >= 0 and isps[n])
            assert isp == (n in sgps)
            assert isp == (next_prime(n) == n)
            assert isp == (n >= 2 and prev_prime(n) == n)
            if N <= NN or rand.random() < 0.1 * math.log(NN) / math.log(N):
                assert isp == is_prime_naive(n)
            if (n & -n) == n:
                print("now at", n)

    test_on(10**5)
    for N in range(2, 20):
        test_on(N)
    test_on(10**7)

if __name__ == '__main__':
    import sys
    assert len(sys.argv) > 1
    if sys.argv[1] == 'test':
        test_some_stuff()
    else:
        n = int(sys.argv[1])
        print(f"{n} is", "prime" if is_prime(n) else "not prime")
### @@ }
