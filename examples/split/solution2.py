from sys import *
sid = 11 if len(argv) <= 1 else int(argv[1])

from random import *
seed(sid)

for cas in range(int(input())):
    input()
    m = {}
    for i, v in enumerate(map(int, input().split())): m.setdefault(v, []).append(i)
    b = [v for i, v in sorted((choice(l), v) for v, l in m.items())]
    print(len(b))
    print(*b)
