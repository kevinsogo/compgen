import argparse
import subprocess
from subprocess import PIPE

parser = argparse.ArgumentParser(description='exact diff judge')
parser.add_argument('input_path', help='input file path')
parser.add_argument('output_path', help="contestant's file path")
parser.add_argument('judge_path', help='judge auxiliary data file path')
parser.add_argument('-c', '--code', default='n/a', help='path to the solution used')
parser.add_argument('-t', '--tc-id', default=None, type=int, help='test case ID, zero indexed')
parser.add_argument('-v', '--verbose', action='store_true', help='print more details')
parser.add_argument('-i', '--identical', action='store_true', help=argparse.SUPPRESS)
args = parser.parse_args()
args = parser.parse_args()
p = subprocess.run(['diff', args.output_path, args.judge_path], stdout=PIPE, encoding='utf-8')

to_print = p.stdout
if len(to_print) > 100+3:
    to_print = to_print[:100] + '...'
assert len(to_print) <= 100+3

if p.returncode:
    print('Incorrect. Diff:')
    print(to_print)

print('Score: ', 1 if p.returncode == 0 else 0)
exit(p.returncode)
