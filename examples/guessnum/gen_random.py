from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

def gen_random(rand, *args):
    n1, n2, m1, m2 = map(int, args[:4])
    return rand.randint(n1, n2), rand.randint(m1, m2)


if __name__ == '__main__':
    write_to_file(format_case, gen_random, argv[1:], stdout)
