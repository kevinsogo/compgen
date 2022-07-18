from sys import argv
i = int(argv[1])
for cas in range(int(input())):
    print(chr(ord(input()[i ^ 1]) ^ ((ord('R') ^ ord('B')) * (i & 1))), flush=True)
