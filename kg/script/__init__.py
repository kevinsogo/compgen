import argparse
import os
import os.path
from sys import stderr

from .script import main

def main_hr(): return main(format='hr')
def main_pg(): return main(format='pg')

