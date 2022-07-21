"""Prints the test data in the correct input format."""

from kg.formatters import * ### @import

@formatter
def format_case(stream, cases, *, print, **kwargs):
    print(len(cases), *cases, sep='\n')
