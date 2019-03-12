from kg.generators import * ### @import
from kg.math.primes import * ### @import

# returns a boolean array of length n+1, where a[i] is True iff i is prime. runs in O(n log log n)
print(prime_sieve(10))
# prints [False, False, True, True, False, True, False, True, False, False, False]

# prints the primes up to n. runs in O(n log log n)
print(get_primes(59))
# prints [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]

# uses miller rabin so it's fast for numbers <= 2^64
# very slow for numbers larger than that, but I'll fix that soon, I promise!
print(is_prime(10**9 + 7))
# prints True

# "is_probable_prime"
# uses miller rabin for all numbers.
# the implementation is guaranteed correct for numbers <= 2^64 (barring bugs)
# uses 18 witnesses for larger numbers, giving a probability of mistake of 1/2^36 ~ 1.45e-11
print(is_prime(22953686867719691230002707821868552601124472329079, guarantee=False)) # prints True

# next and previous prime. for numbers > 2^64
# pass guarantee=False for speed (in exchange for absolute certainty)
print(next_prime(90))  # prints 97
print(next_prime(97))  # prints 97
print(next_prime(22953686867719691230002707821868552601124472329062, guarantee=False)) # prints the prime above
print(prev_prime(96))  # prints 89
print(prev_prime(1))   # kg.math.primes.MathError: There is no prime <= 1
