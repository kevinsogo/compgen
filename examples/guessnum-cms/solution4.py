from random import *
def rand_query():
    x = randint(-10**9, 10**9)
    print('ask', x, flush=True)
    return x - int(input())
[v] = {rand_query() for it in range(int(input()))}
print('answer', v)
