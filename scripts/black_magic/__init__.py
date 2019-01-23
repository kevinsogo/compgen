#!/usr/bin/python

'''
Recursively expand imports in several files.
'''

from __future__ import print_function

from sys import *
from compgen import apply_after

def expand_imports(files, get_contents, get_name, keep_future_imports=True):
    contents = {}
    for file in files:
        with open(file) as f:
            contents[file] = list(get_contents(file, f))
            assert contents[file] is not None, "{} not processed properly!".format(file)


    name_of_file = {file: get_name(file) for file in files}

    file_of_name = {name: file for file, name in name_of_file.items()}

    def get_imported(parts):
        if len(parts) == 4 and parts[:1] + parts[2:] == ['from', 'import', '*']:
            return parts[1]

    def clear_future_imports(lines):
        found_future_import = False
        for line in lines:
            parts = line.strip().split()
            if parts[:3] == ['from', '__future__', 'import']:
                curr_future_import = parts[3:]
                if found_future_import and set(found_future_import) != set(curr_future_import):
                    print('WARNING!!! The set of future imports is not unique so it might not work:\n({}) vs ({})'.format(' '.join(found_future_import), ' '.join(curr_future_import)))
                skip = not keep_future_imports or found_future_import
                found_future_import = curr_future_import
                if skip: continue
            yield line


    @apply_after(clear_future_imports)
    def expand_imports(file, visiting, visited):
        if file in visiting:
            print("Infinite loop!", file=stderr)
            exit(1)
        visiting.add(file)
        for line in contents[file]:
            imported = get_imported(line.strip().split())
            if imported in file_of_name:
                fimported = file_of_name[imported]
                if fimported not in visited:
                    for line in expand_imports(fimported, visiting, visited):
                        yield line
            else:
                yield line
        visiting.remove(file)
        visited.add(file)

    expanded = {}
    deps = {}
    for file in sorted(contents):
        deps[file] = set()
        expanded[file] = list(expand_imports(file, set(), deps[file]))

    return expanded, deps

