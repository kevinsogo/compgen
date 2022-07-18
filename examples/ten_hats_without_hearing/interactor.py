"""Interacts with the solution. Useful for tasks with hidden information."""

from sys import *
from kg.interactors import * ### @import

@interactor
def interact(input_stream, *user_streams, output_stream=None, **kwargs):
    [t] = input_stream.read.int().eoln
    for user in user_streams:
        user.print(t)

    n = len(user_streams)
    if n % 2 != 0:
        raise Fail("The number of prisoners must be even")

    def valid_str(s):
        return len(s) == n and all(ch in {'R', 'B'} for ch in s)
    results = [0, 0]
    for cas in range(t):
        [target] = input_stream.read.token().eoln
        ensure(valid_str(target), "Bad string in input", Fail)
        for i, user in enumerate(user_streams):
            user.print(target[:i] + '?' + target[i+1:])
        gots = []
        for user in user_streams:
            [got] = user.read.token().eoln
            gots.append(got)
        results[all(valid_str(got) for got in gots) and sum(got == target for got in gots) >= n // 2] += 1

    lost, won = results
    return 1.0 if lost == 0 else 0.0

if __name__ == '__main__':
    interact_with(interact, force_verbose=True)
