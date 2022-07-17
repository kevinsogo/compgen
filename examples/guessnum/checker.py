from kg.checkers import * ### @import

V = 10**9

@checker('tokens', 'raw_lines', 'raw_lines', extra_chars_allowed=['judge'])
@default_score
def check(input_stream, output_stream, judge_stream, **kwargs):
    [n, m] = input_stream.read.int().int()
    while True:
        [action, value] = output_stream.read.token().space.token().eoln
        value = int(value)
        ensure(abs(value) <= V, lambda: Fail(f"Out of bounds value not detected by interactor: {action} {value}"))
        if action == 'answer':
            if n != value: raise Wrong(f"Wrong answer! {n} != {value}")
            break
        elif action == 'ask':
            ...
        else:
            raise Fail(f"Unknown action not detected by interactor: {action} {value}")

if __name__ == '__main__':
    check_files(check, title="Guess Num")
