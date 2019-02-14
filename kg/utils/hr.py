import json

from .utils import * ### @import 'kg.utils.utils'

class HRError(Exception): ...

def hr_iterate(subtasks_files, *, compiled=False):
    if compiled:
        yield from subtasks_files
    else:
        for left, right, subtasks in subtasks_files: yield (left, right), subtasks

def hr_parse_subtasks(valid_subtasks, subtasks_files, *, compiled=False):
    subtasks_of = {}
    last_file_of = {subtask: -1 for subtask in valid_subtasks}

    for (left, right), subtasks in hr_iterate(subtasks_files, compiled=compiled):
        ensure(0 <= left <= right <= 99, lambda: HRError(f"HRChecker: range ({left} {right}) is invalid"))
        ensure(len(set(subtasks)) == len(subtasks), lambda: HRError(f"HRChecker: duplicate subtasks in list: {subtasks}"))
        ensure(set(subtasks) <= set(valid_subtasks), lambda: HRError(f"HRChecker: subtask list invalid: {subtasks}. allowed = {valid_subtasks}"))
        for idx in range(left, right + 1):
            ensure(idx not in subtasks_of, lambda: HRError(f"HRChecker: {idx} has already appeared!"))
            subtasks_of[idx] = subtasks
            for subtask in subtasks:
                last_file_of[subtask] = max(last_file_of[subtask], idx)

    ensure(min(last_file_of.values()) >= 0, "HRChecker: some subtasks weren't represented by any files!", HRError)
    ensure(len(set(last_file_of.values())) == len(last_file_of), "HRChecker: The last file of any subtask must be unique to that subtask!!", HRError)

    return subtasks_of, last_file_of
