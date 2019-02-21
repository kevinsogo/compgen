import argparse
from sys import *

from .compiler import compile_lines

def main():
    parser = argparse.ArgumentParser(description='A tool that is not meant for you.')
    parser.add_argument('-p', '--parse-only', action='store_true')

    args = parser.parse_args()

    def load_module(module):
        return iter(['imported ' + module] * 3)

    def get_module_id(x, c):
        return x.lstrip('.')

    def lines():
        for line in stdin: yield line.rstrip('\n')

    lines = list(lines())
    for fmt in 'local', 'kg', 'pg', 'hr', 'pc2':
        print('@@@@@@@@@@@@ trying', fmt)
        for line in compile_lines(lines,
            load_module=load_module,
            get_module_id=get_module_id,
            format=fmt,
            details=None,
            valid_subtasks=[],
            subtasks_files = [],
            snippet=False,
            subtasks_only=False,
        ):
            print(line)
        print('@@@@@@@@@@@@ done')

if __name__ == '__main__': main()
