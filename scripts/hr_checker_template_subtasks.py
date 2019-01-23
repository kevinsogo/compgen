{expanded_code}

def _run_custom_checker(t_obj, r_obj):
    chk.run('hr', t_obj, r_obj, print_message={print_message})








# list of valid subtasks for this problem
valid_subtasks = [{valid_subtasks}]

# list of subtasks per file. FORMAT: ((left, right), [list of subtasks])
subtasks_files = [
{subtasks_files}
]

# change this for every problem just to be safe
tmp_filename_base = '/tmp/hr_custom_checker_{filename_base}_'

# under the testcases tab, if a file is the last file for some subtask (which should be unique),
# set the weight of the file to be the number of points for the subtask.
# set the weight of the remaining files to be 0.  

import json
subtasks_of = {{}}
last_file_of = {{subtask: -1 for subtask in valid_subtasks}}

for (left, right), subtasks in subtasks_files:
    ensure(0 <= left <= right <= 99, "range (%s %s) is invalid" % (left, right))
    ensure(len(set(subtasks)) == len(subtasks), "duplicate subtasks in list: %s" % subtasks)
    ensure(set(subtasks) <= set(valid_subtasks), "subtask list invalid: %s. allowed = %s" % (subtasks, valid_subtasks))
    for idx in xrange(left, right + 1):
        ensure(idx not in subtasks_of, "%s has already appeared!" % idx)
        subtasks_of[idx] = subtasks
        for subtask in subtasks:
            last_file_of[subtask] = max(last_file_of[subtask], idx)

ensure(min(last_file_of.values()) >= 0, "some subtasks weren't represented by any files!")
ensure(len(set(last_file_of.values())) == len(last_file_of), "The last file of any subtask must be unique to that subtask!!")

def clear_tmp(filename):
    try:
        import os
        os.remove(filename)
    except OSError:
        pass

def run_custom_checker(t_obj, r_obj):
    tmp_filename = tmp_filename_base + str(sum(map(ord, t_obj.submission_code_path)))

    test_id = t_obj.testcase_id
    ensure(test_id in subtasks_of, "Testcase id invalid: %s" % (test_id))
    curr_subtasks = subtasks_of[test_id]

    if test_id == 0:
        previous_scores = {{}}
    else:
        try:
            with open(tmp_filename) as f:
                previous_scores = json.load(f)
            previous_scores = {{int(k): v for k, v in previous_scores.items()}}
        except Exception:
            previous_scores = {{}}


    for subtask in valid_subtasks:
        previous_scores.setdefault(subtask, 1.0)

    _run_custom_checker(t_obj, r_obj)

    for subtask in curr_subtasks:
        previous_scores[subtask] = min(previous_scores[subtask], r_obj.score)

    r_obj.score = 0

    for subtask in curr_subtasks:
        if last_file_of[subtask] == test_id:
            r_obj.score = previous_scores[subtask]
            break

    with open(tmp_filename, 'w') as f:
        json.dump(previous_scores, f)
