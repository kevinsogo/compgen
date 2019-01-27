maxn = 0
for cas in range(int(input())):
    maxn = max(maxn, int(input()))
    input()
if maxn <= 10:    print(1)
if maxn <= 1000:  print(2)
if maxn <= 10**5: print(3)
