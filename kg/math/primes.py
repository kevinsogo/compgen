"""
This includes the Miller-rabin primality test, with a version valid for all 64-bit unsigned integers (hopefully no bugs!).
Sometimes wrong for numbers greater
"""

from itertools import chain
from random import randrange
from sys import stderr, argv

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

_sieve_is_prime = []
_sieve_primes = []
def _set_sieve(n):
    _sieve_is_prime[:] = prime_sieve(n)
    _sieve_primes[:] = get_primes(n, _sieve_is_prime)

_small_primes = []
def _set_small(s):
    _small_primes[:] = get_primes(s, _sieve_is_prime)

_set_sieve(10**5)
_set_small(80)

def _check_composite(n, s, d, a):
    """ check compositeness of n with witness a. (n,s,d) should satisfy d*2^s = n-1 and d is odd """
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

def is_prime_miller_rabin(n, *, more_witnesses=()): ### @@if False {
    """
    returns True if n is probably prime, and False if n is definitely not prime.
    if n < 2^64, then is_prime(n) never returns a wrong answer. (hopefully!)
    """
    ### @@}
    # if too small, check _sieve_is_prime   ### @if False
    if n < len(_sieve_is_prime): return _sieve_is_prime[n]
    # check divisibility with _small primes   ### @if False
    if any(n % p == 0 for p in _small_primes): return False
    # find (d,s) such that d*2^s = n-1 with d odd   ### @if False
    d, s = n - 1, 0
    while not d & 1: d >>= 1; s += 1
    # find the best set of witnesses   ### @if False
    for bound, bound_ws in _witnesses_bounds:
        if n < bound:
            best_witnesses = bound_ws
            break
    else:
        best_witnesses = _i64_witnesses
    # check compositeness with the witnesses   ### @if False
    for a in chain(best_witnesses, more_witnesses):
        if _check_composite(n, s, d, a): return False
    return True

def is_prime_naive(n):
    if n < 2: return False
    if n < len(_sieve_is_prime): return _sieve_is_prime[n]
    for p in _sieve_primes:
        if p * p > n: break
        if n % p == 0: return False
    while p * p <= n:
        if n % p == 0: return False
        p += 1
    return True
# TODO implement some O(n^(1/3)) primality test/factorization (perhaps Fermat+Lehman?) or something, ### @if False
# O(n^(1/4)) also possible [SQUFOF algorithm] but may be too hard to implement and verify ### @if False

def is_prime(n, *, guarantee=True):
    if not is_prime_miller_rabin(n, more_witnesses=(randrange(2, 10**18) for i in range(11 if n >= 2**64 else 0))):
        return False
    if guarantee and n >= 2**64:
        print(f'WARNING: falling back to slow algorithm for primality testing {n}', file=stderr)
        return is_prime_naive(n)
    return True

def next_prime(n, *, guarantee=True):
    while not is_prime(n, guarantee=guarantee): n += 1
    return n

def prev_prime(n, *, guarantee=True):
    if n < 2: raise MathError(f"There is no prime <= {n}")
    while not is_prime(n, guarantee=guarantee): n -= 1
    assert n >= 2
    return n

### @@if False {
if __name__ == '__main__':
    n = int(argv[1])
    print(f"{n} is", "prime" if is_prime(n) else "not prime")
### @@}
