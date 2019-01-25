maxn = 0
for cas in range(int(input())):
    n = int(input())
    input()
    maxn = max(n, maxn)
if maxn <= 10: print(1)
if maxn <= 1000: print(2)
print(3)
