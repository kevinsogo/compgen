from random import *
input()
v = randrange(-10**9, 10**9+1)
print('ask', v, flush=True)
v -= int(input())
while random() < 0.2: v += 1
while random() < 0.2: v -= 1
if random() < 0.2:
    if randrange(2):
        print('ansah', v)
    else:
        v = choice([-2**33, 2**33])
        print('answer', v)
else:
    print('answer', v)
