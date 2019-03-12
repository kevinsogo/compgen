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
