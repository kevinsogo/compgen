from sys import *
from kg.interactors import * ### @import

MAX_ABS = 10**9


@interactor
@default_score
def interact(input_file, user, *, output_file, **kwargs):
    target, moves = map(int, input_file.readline().split())
    if moves < 0: raise Fail("invalid number of moves!")
    print(moves, file=user, flush=True)
    while True:
        line = user.readline()
        output_file.write(line)
        tok, value = line.rstrip('\n').split(' ')
        value = int(value)
        if abs(value) > MAX_ABS: raise Wrong("value not in required range")
        if tok == "answer":
            return  # got the answer. pass to checker
        elif tok == "ask":
            if moves == 0: raise Wrong("ran out of moves")
            moves -= 1
            print(value - target, file=user, flush=True)
        else:
            raise Wrong(f"unknown action: {tok}")


if __name__ == '__main__':
    interact()


