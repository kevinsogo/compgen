from sys import *
from kg.interactors import * ### @import

MAX_ABS = 10**9


@interactor
def interact(input_file, user, *, output_file, **kwargs):
    target, moves = map(int, input_file.readline().split())
    if moves < 0: raise Fail("invalid number of moves!")
    user.print(moves)
    while True:
        line = user.readline()
        output_file.write(line)
        tok, value = line.rstrip('\n').split(' ')
        value = int(value)
        if abs(value) > MAX_ABS: raise Wrong("value not in required range")
        if tok == "answer":
            return 1.0 # got the answer. pass to checker
        elif tok == "ask":
            if moves == 0: raise Wrong("ran out of moves")
            moves -= 1
            user.print(value - target)
        else:
            raise Wrong(f"unknown action: {tok}")


if __name__ == '__main__':
    interact()


