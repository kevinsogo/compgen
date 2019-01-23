from __future__ import print_function

import re

assert raw_input() == 'DETAILS', "invalid stdin data... where did you get this??"

def input_index(file):
    return int(re.search(r'input/input(\d+)\.txt$', file).groups()[0])

subs = {}
while raw_input() == 'FILE':
    idx = input_index(raw_input())
    subs[idx] = sorted(set(map(int, raw_input().split())))

valid_subtasks = sorted(set(sum(subs.values(), [])))

def raw_sub_files():
    for idx in sorted(subs):
        yield (idx, idx), subs[idx]

def is_compatible(((a, b), l), ((A, B), L)):
    assert a <= b
    assert A <= B
    return a + 1 == A and l == L

def merge(((a, b), l), ((A, B), L)):
    return (a, B), l

def merge_adj(seq):
    prev = None
    for v in seq:
        if prev and is_compatible(prev, v):
            prev = merge(prev, v)
        else:
            if prev: yield prev
            prev = v

    if prev: yield prev

print('''{
    "valid_subtasks": %s,
    "subtasks_files": [
        %s
    ]
}''' % (
        valid_subtasks,
        (',\n' + ' '*8).join(('[[%s, %s], %s]') % (a, b, l) for (a, b), l in merge_adj(raw_sub_files())),
    ))
