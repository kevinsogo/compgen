from sys import *
from kg.interactors import * ### @import

MAX_ABS = 10**9

lim = Bounds(value = abs(+Var) <= MAX_ABS)

@interactor
def interact(input_stream, user_stream, *, output_stream=None, **kwargs):
    [target, moves] = input_stream.read.int().space.int().eoln
    if moves < 0: raise Fail("invalid number of moves!")
    user_stream.print(moves)
    while True:
        [tok, value] = user_stream.read.token().space.int(lim.value).eoln
        if output_stream: output_stream.print(tok, value)
        if tok == "answer":
            return 1.0 # got the answer. pass to checker
        elif tok == "ask":
            if moves == 0: raise Wrong("ran out of moves")
            moves -= 1
            user_stream.print(value - target)
        else:
            raise Wrong(f"unknown action: {tok}")


if __name__ == '__main__':
    interact_with(interact)


