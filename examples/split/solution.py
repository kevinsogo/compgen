for cas in range(int(input())):
    input()
    m = {}
    b = [m.setdefault(a, a) for a in map(int, input().split()) if a not in m]
    print(len(b))
    print(*b)
