from kg.checkers import * ### @import

V = 10**9

@set_checker(no_extra_chars=['input', 'output'])
@default_score
def check_solution(input_file, output_file, judge_file, **kwargs):
    n, m = map(int, next(input_file).split())
    while True:
        action, value = next(output_file).split()
        value = int(value)
        ensure(abs(value) <= V, lambda: Fail(f"Out of bounds value not detected by interactor: {action} {value}"))
        if action == 'answer':
            if n != value: raise WA(f"Wrong answer! {n} != {value}")
            break
        elif action == 'ask':
            ...
        else:
            raise Fail(f"Unknown action not detected by interactor: {action} {value}")

if __name__ == '__main__': chk(title="Guess Num")
