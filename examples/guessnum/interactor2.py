from sys import *
from kg.interactors import * ### @import

MAX_ABS = 10**9


@interactor
def interact(input_stream, user_stream, *, output_stream=None, **kwargs):
    target, moves = map(int, next(input_stream).split())
    if moves < 0: raise Fail("invalid number of moves!")
    user_stream.print(moves)
    while True:
        line = next(user_stream)
        print(line, file=output_stream)
        tok, value = line.rstrip('\n').split(' ')
        value = int(value)
        if abs(value) > MAX_ABS: raise Wrong("value not in required range")
        if tok == "answer":
            return 1.0 # got the answer. pass to checker
        elif tok == "ask":
            if moves == 0: raise Wrong("ran out of moves")
            moves -= 1
            print(value - target, file=user_stream)
        else:
            raise Wrong(f"unknown action: {tok}")


if __name__ == '__main__':
    interact_with(interact)


