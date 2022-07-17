from kg.formatters import * ### @import

@formatter
def format_case(stream, cases, *, print, **kwargs):
    print(len(cases))
    for arr in cases:
        print(len(arr))
        print(*arr)
