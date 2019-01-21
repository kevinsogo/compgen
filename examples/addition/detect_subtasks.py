maxn = 0
for cas in xrange(input()):
    n = input()
    raw_input()
    maxn = max(n, maxn)
if maxn <= 10: print 1,
if maxn <= 1000: print 2,
print 3
