from sys import *
sid = 11 if len(argv) <= 1 else int(argv[1])

from random import *
seed(sid)

for cas in xrange(input()):
    raw_input()
    m = {}
    for i, v in enumerate(map(int, raw_input().split())): m.setdefault(v, []).append(i)
    b = [v for i, v in sorted((choice(l), v) for v, l in m.items())]
    print len(b)
    print ' '.join(map(str, b))
