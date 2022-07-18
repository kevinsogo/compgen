from sys import argv, stderr
from random import *
seed(11)

n = 10
i = int(argv[1])
assert 0 <= i < n
for cas in range(int(input())):
    s = input()
    cr, cb = map(s.count, 'RB')
    print(choice(['R' * (cr >= cb), 'B' * (cb >= cr)]) , flush=True)
