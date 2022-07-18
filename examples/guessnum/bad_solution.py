import time
import hashlib
from random import *
seed(int(hashlib.sha224(input().encode('utf-8')).hexdigest(), 16))

v = randrange(-10**9, 10**9+1)
print('ask', v, flush=True)
v -= int(input())
while random() < 0.2: v += 1
while random() < 0.2: v -= 1
if random() < 0.3:
    if randrange(3) == 0:
        print('ansah', v)
    elif randrange(2) == 0:
        v = randint(-2**33, 2**33)
        print('answer', v)
    else:
        time.sleep(30)
        print('answer', v)
else:
    print('answer', v)
