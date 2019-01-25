from sys import *
import subprocess

ret = subprocess.call(['diff', argv[2], argv[3]])
print('Score: ', 1 if ret == 0 else 0)
exit(ret)

# TODO make this @import from compgen.checkers
