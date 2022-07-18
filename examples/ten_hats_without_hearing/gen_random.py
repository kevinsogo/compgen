"""Generates random tests."""

from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

@listify
def gen_random(rand, *args):
    T, N = map(int, args[:2])
    prob = float(args[2])
    for cas in range(T):
        if prob < 0:
            ct = rand.randint(0, N)
            yield ''.join(rand.shuffled('R' * ct + 'B' * (N - ct)))
        else:
            yield ''.join('R' if rand.random() < prob else 'B' for i in range(N))


if __name__ == '__main__':
    write_to_file(format_case, gen_random, argv[1:], stdout)
