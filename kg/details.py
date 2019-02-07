import json

from .programs import *
from .formats import *

script_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(script_path, 'data', 'defaults.json')) as f:
    defaults = json.load(f)

valid_keys = set(defaults) | {"comments", "extras"}


def detector_from_validator(validator, relpath=None):
    if validator:
        return Program("!fromvalidator", validator.compile, ["kg-subtasks", "-c"] + validator.run + ["--"], relpath=relpath)


class Details(object):
    def __init__(self, details={}, source=None, relpath=None):
        self.details = details
        self.source = source
        self.relpath = relpath
        self.valid_subtasks = self.details.get('valid_subtasks', [])

        # data validation
        if not all(isinstance(v, int) for v in self.valid_subtasks):
            raise ValueError("Subtask values must be ints")

        if len(set(self.valid_subtasks)) != len(self.valid_subtasks):
            raise ValueError("Duplicate values in valid_subtasks")

        for key in ['title', 'time_limit']:
            setattr(self, key, self.details.get(key, defaults.get(key)))

        for key in ['validator', 'checker', 'model_solution', 'subtask_detector', 'judge_data_maker']:
            setattr(self, key, self._maybe_prog(self.details.get(key, defaults.get(key)), key=key))

        for key in ['generators', 'other_programs']:
            setattr(self, key, [self._maybe_prog(x, key=key) for x in self.details.get(key, [])])

        if not self.subtask_detector:
            self.subtask_detector = detector_from_validator(self.validator, relpath=relpath)
            assert (not self.subtask_detector) == (not self.validator)


        if not self.judge_data_maker:
            self.judge_data_maker = self.model_solution

        self.testscript = self.details.get('testscript')

        # subtasks_files
        self.subtasks_files = self.details.get('subtasks_files', "")

        for key in ['testscript', 'subtasks_files']:
            setattr(self, key, attach_relpath(relpath, getattr(self, key)))

        # TODO move this check to the appropriate place, e.g., only when subtasks_files is actually accessed
        # if self.subtasks_files and os.path.isfile(self.subtasks_files):
        #     with open(self.subtasks_files) as f:
        #         ff = f.read()
        #     if ff.strip():
        #         subf = json.loads(ff)
        #         found_files = set()
        #         for low, high, subs in subf:
        #             if low > high: raise ValueError("Invalid range in subtasks_files: {} {}".format(low, high))
        #             for idx in range(low, high + 1):
        #                 if idx in found_files: raise ValueError("File {} appears multiple times in subtasks_files: {}".format(idx))
        #                 found_files.add(idx)

        #             if not subs:
        #                 raise ValueError("Empty list of subtasks in subtasks_files")

        #             if not (set(subs) <= set(self.valid_subtasks)):
        #                 raise ValueError("Invalid subtasks found in subtasks_files: {}".format(' '.join(sorted(set(subs) - set(self.valid_subtasks)))))

        # check for extra keys
        for key in self.details:
            if key not in valid_keys:
                raise ValueError("Key {} invalid in details.json. If you wish to add extra data, place it under 'comments' or 'extras'".format(repr(key)))

        super(Details, self).__init__()

    @classmethod
    def from_loc(cls, loc, relpath=None):
        details_file = attach_relpath(relpath, 'details.json')
        if not loc and os.path.isfile(details_file): loc = details_file
        if loc:
            with open(loc) as f:
                return cls(json.load(f), source=loc, relpath=relpath)

    @classmethod
    def from_format_loc(cls, fmt, loc, relpath=None):
        details = cls(relpath=relpath)
        if is_same_format(fmt, 'kg'):
            details = cls.from_loc(loc, relpath=relpath) or details
        return details

    def _maybe_prog(self, v, key=None):
        # special parsing for checker
        if key == 'checker':
            diff_pref = '!diff.'
            if isinstance(v, str) and v.startswith(diff_pref): 
                v = os.path.join(script_path, 'diff', v[len(diff_pref):] + '.py')
        prog = Program.from_data(v, relpath=self.relpath) if v else None
        return prog

    def serialize(self):
        ... # not implemented yet. returns a dict to be json'ed

