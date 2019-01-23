for cas in xrange(input()):
    raw_input()
    m = {}
    b = [m.setdefault(a, a) for a in map(int, raw_input().split()) if a not in m]
    print len(b)
    print ' '.join(map(str, b))
