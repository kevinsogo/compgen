from kg.formatters import * ### @import

@formatter
def print_to_file(file, cases, *, print):
    print(len(cases))
    for arr in cases:
        print(len(arr))
        print(*arr, sep=' ')
