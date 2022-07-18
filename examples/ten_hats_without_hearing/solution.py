from sys import argv
i = int(argv[1])
for cas in range(int(input())):
    print('RB'[(input().count('R') ^ i) & 1], flush=True)
