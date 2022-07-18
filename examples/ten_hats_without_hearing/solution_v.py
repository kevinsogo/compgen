from sys import argv
n = 10
i = int(argv[1])
assert 0 <= i < n
for cas in range(int(input())):
    s = input()
    assert s[i] == '?'
    assert all(s[j] in {'R', 'B'} for j in range(n) if j != i)
    print(chr(ord(s[i ^ 1]) ^ ((ord('R') ^ ord('B')) * (i & 1))), flush=True)
