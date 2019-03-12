<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE. -->
<!-- Edit docs_src/GENERATORS.md instead, then run './makedocs'. -->


Note: this is still WIP


# Grid generators  

Specialized grid generators exist in the `kg.grids.generators` package:

```python
from kg.grids.generators import * ### @import
```

Sample usage:

```python
from kg.generators import * ### @import
from kg.grids.generators import * ### @import

def draw_grid(grid):
    ''' draws a grid '''
    for row in grid: print(*row)
    print()

rand = KGRandom(11) # create a PRNG with seed


# a random grid of booleans
draw_grid(gen_random_grid(rand, 5, 8))
'''
Prints the following:

True False False True True False True True
False True True False True True False True
True True False False True False False True
True True False False False True True False
True True True True True True True True
'''


# a random grid of two things
draw_grid(gen_random_grid(rand, 8, 11, '.', '#'))
'''
. # # . . # . # . # .
# . . . # . # . . # #
. # # # . # . . # # .
. . . # . . # # # # #
. . . # . . # # . . .
# . . # # . # # # . .
. # # # # # . # . # .
# # . # # . . # . . .
'''


# a random grid of three things
draw_grid(gen_random_grid(rand, 8, 11, '.', '#', 'X'))
'''
X # X # # X # # # . .
. X # . # # # X . X #
. X X X . # . X . # #
. # . X X . X X X X .
# # # . . X . . # . .
X . # # # # . X X # #
. X . # X # . # X . X
# X # X X . . X # # #

'''

# it can be anything. here's a random grid of digits
draw_grid(gen_random_grid(rand, 8, 11, *range(10)))
'''
2 9 4 5 7 4 9 4 5 5 6
3 3 7 3 1 7 0 2 1 2 7
0 4 4 4 0 2 6 4 9 7 0
1 4 6 0 6 3 6 9 9 0 3
8 8 3 8 5 3 4 2 8 1 5
8 8 9 5 7 7 9 7 3 4 8
5 9 0 8 8 8 9 2 4 6 6
5 3 5 9 7 6 0 6 8 0 7
'''

# 4 times more '.'s than '#'s
draw_grid(gen_random_grid(rand, 8, 11, Tile('.', weight=4),
                                       Tile('#', weight=1)))
'''
. . . . . # . . . . .
# . . # . . . . # . .
. . . . . . . # # # #
. . . # . . . . . # .
. . . . . . . . . . .
. # . . . . # . # . .
. . . . . . . . . . .
. . # . . . # . . . .
'''

# alternatively...
draw_grid(gen_random_grid(rand, 8, 11, Tile('.', weight=0.8),
                                       Tile('#', weight=0.2)))
'''
. . . . . . . . . . #
. . . . . . . . # . .
. . . . . # # . . . .
. # . . . . . . . . .
. # . . . . . . . . .
. . . . . # . . . . #
. # . . . # . . . . .
. . . . . . . . . . .
'''

# has exactly one starting point and exactly two ending points
draw_grid(gen_random_grid(rand, 8, 11, Tile('.', weight=4),
                                       Tile('#', weight=1),
                                       Tile('S', ct=1),
                                       Tile('E', ct=2)))
'''
# . # . . . . . . . .
. # . . . . E . . . .
# . # . . . # . . . .
# # . # . . . . . . #
. . . . # E # S . # #
# . . . . . . . . . .
. . . # . # . . . . .
. . # . . # . . . # .
'''

# has exactly one starting point and between 1 and 5 ending points
draw_grid(gen_random_grid(rand, 8, 11, Tile('.', weight=4),
                                       Tile('#', weight=1),
                                       Tile('S', ct=1),
                                       Tile('E', minct=1, maxct=5)))
'''
# . . . . . . # . . .
. . # # . . . E . . S
. # . . . . . . E # .
. . . . # . . . . # #
# . . . . . . # . . E
. . . . . # . . . E #
. . E . . . # . . . #
. . . . . . . . . # .
'''

# 4 times more '.'s than walls. Walls can be '#' or 'X' with equal probability.
draw_grid(gen_random_grid(rand, 8, 11, Tile('.', weight=4),
                                       Tile('#', 'X', weight=1)))
'''
. . . X . . . . . . .
. X . X . . # . . . .
. . . . . . . . X . .
. X . . . . . X . . #
. . . . . . . . . . .
. . . . . . . . . # .
. . . . X . # . . X .
# . X . . . . X . X .
'''
```


# Graph generators

Specialized graph generators exist in the `kg.grids.generators` package:

```python
from kg.graphs.generators import * ### @import
```

This includes random tree generation.

Sample usage: Under construction.


# Primes  

You can generate primes with the help of the `kg.math.primes` package:

```python
from kg.math.primes import * ### @import
```

Sample usage:

```python
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
```
