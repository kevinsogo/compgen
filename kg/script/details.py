from collections import OrderedDict
import json
from sys import stderr

from .programs import *
from .formats import *
from .utils import *

with open(os.path.join(kg_data_path, 'defaults.json')) as f:
    defaults = json.load(f)

valid_keys = set(defaults) | {"comments", "extras"}


def detector_from_validator(validator, relpath=None):
    if validator:
        return Program("!detector_from_validator", validator.compile,
                ["kg-aux", "subtasks-from-validator", "-q", "-c"] + ['___' + part for part in validator.run] + ["--"],
                relpath=relpath)

class Subtask(object):
    def __init__(self, subtask):
        if isinstance(subtask, int):
            subtask = {"id": subtask}
        self.id = int(subtask['id'])
        self.score = subtask.get('score')

        # data validation
        if not isinstance(self.id, int):
            raise TypeError("Subtask values must be ints")

        # TODO check that 'score' is int, float, Decimal, etc. or None
            
        super().__init__()

    def serialize(self):
        raise NotImplementedError # not implemented yet. returns a dict to be json'ed

class Details(object):
    def __init__(self, details={}, source=None, relpath=None):
        self.details = details
        self.source = source
        self.relpath = relpath

        # make it a subtask list
        self.valid_subtasks = OrderedDict((subtask.id, subtask) for subtask in map(Subtask, self.details.get('valid_subtasks', [])))

        # data validation
        if len(set(self.valid_subtasks)) != len(self.valid_subtasks):
            raise ValueError("Duplicate values in valid_subtasks")

        for key in ['cms_options']:
            setattr(self, key, self.details.get(key, defaults.get(key) or {}))

        for key in ['title', 'time_limit']:
            setattr(self, key, self.details.get(key, defaults.get(key)))

        for key in ['validator', 'checker', 'interactor', 'model_solution', 'subtask_detector', 'judge_data_maker']:
            setattr(self, key, self._maybe_prog(self.details.get(key, defaults.get(key)), key=key))

        for key in ['generators', 'other_programs']:
            setattr(self, key, [self._maybe_prog(x, key=key) for x in self.details.get(key, [])])

        self.scoring = self._get_scoring(self.details.get('scoring'))

        if not self.subtask_detector:
            self.subtask_detector = detector_from_validator(self.validator, relpath=relpath)
            assert (not self.subtask_detector) == (not self.validator)

        # prefix of generators
        for generator in self.generators:
            if not os.path.basename(generator.filename).startswith('gen_'):
                warn_print("It is preferable to prefix generator filenames with 'gen_' "
                          f"(found {generator.filename!r})", file=stderr)

        if not self.judge_data_maker:
            self.judge_data_maker = self.model_solution

        self.testscript = self.details.get('testscript')

        # subtasks_files
        self.subtasks_files = self.details.get('subtasks_files', "")

        self.statement = self._get_statement(self.details.get('statement'))

        for key in ['testscript', 'subtasks_files']:
            setattr(self, key, attach_relpath(relpath, getattr(self, key)))

        # check for extra keys
        for key in self.details:
            if key not in valid_keys:
                raise ValueError(f"Key {key!r} invalid in details.json. If you wish to add extra data, "
                        "place it under 'comments' or 'extras'")

        super().__init__()

    @classmethod
    def from_loc(cls, loc, relpath=None):
        details_file = attach_relpath(relpath, 'details.json')
        if not loc and os.path.isfile(details_file): loc = details_file
        if loc:
            with open(loc) as f:
                try:
                    loc_json = json.load(f)
                except Exception:
                    err_print(f"An exception occurred while trying to load {loc}...")
                    raise
            return cls(loc_json, source=loc, relpath=relpath)

    @classmethod
    def from_format_loc(cls, fmt, loc, relpath=None):
        details = cls(relpath=relpath)
        if is_same_format(fmt, 'kg'):
            details = cls.from_loc(loc, relpath=relpath) or details
        return details

    def load_subtasks_files(self):
        if self.subtasks_files and os.path.isfile(self.subtasks_files):
            with open(self.subtasks_files) as f:
                subf = json.load(f)
            found_files = set()
            for low, high, subs in subf:
                if low > high: raise ValueError(f"Invalid range in subtasks_files: {low} {high}")
                for idx in range(low, high + 1):
                    if idx in found_files: raise ValueError(f"File {idx} appears multiple times in subtasks_files")
                    found_files.add(idx)

                if not subs:
                    raise ValueError("Empty list of subtasks in subtasks_files")

                if not (set(subs) <= set(self.valid_subtasks)):
                    raise ValueError(f"Invalid subtasks found in subtasks_files: " +
                            ' '.join(map(str, sorted(set(subs) - set(self.valid_subtasks)))))

            return subf

    def dump_subtasks_files(self, subtasks_files):
        with open(self.subtasks_files, 'w') as f:
            f.write('[\n' + '\n'.join(f'    {list(x)},' for x in subtasks_files).rstrip(',') + '\n]')

    def _maybe_prog(self, v, key=None):
        # special parsing for checker
        if key == 'subtask_detector':
            if v == '!detector_through_validator':
                return Program("!detector_through_validator", self.validator.compile,
                        self.validator.run + ["--detect-subtasks"],
                        relpath=self.relpath)
        if key == 'checker':
            diff_pref = '!diff.'
            if isinstance(v, str) and v.startswith(diff_pref): 
                v = os.path.join(kg_path, 'diff', v[len(diff_pref):] + '.py')
        prog = Program.from_data(v, relpath=self.relpath) if v else None
        return prog

    def _get_scoring(self, scoring):
        if scoring is None:
            if self.binary:
                # the default for binary tasks is to take the minimum across all tests
                scoring = '!min'
            else:
                # the default for tasks with subtasks is to take the minimum for each
                # subtask group and then add the (weighted) scores
                scoring = {
                    'overall': '!sum',
                    'per_subtask': '!min',
                }

        if isinstance(scoring, str):
            scoring = {'overall': scoring}

        # check type
        if not isinstance(scoring, dict):
            raise TypeError(f"The scoring object must be str or dict, got {type(scoring)}")

        scoring.setdefault('per_subtask', '!min')
        scoring.setdefault('default_weight', 1)

        # check values
        if 'overall' not in scoring:
            raise ValueError("The scoring object must have the 'overall' key")

        scoring_keys = {'overall', 'per_subtask', 'default_weight'}
        if not all(key in scoring_keys for key in scoring):
            raise ValueError(f"The scoring object must only have the following keys: {scoring_keys}")

        overall_values = {'!ave', '!sum', '!min'}
        if scoring['overall'] not in overall_values:
            raise ValueError(
                    f"The scoring object's value for 'overall' must be in {overall_values},"
                    f"got {scoring['overall']}")

        per_subtask_values = {'!ave', '!min'}
        if scoring['per_subtask'] not in per_subtask_values:
            raise ValueError(
                    f"The scoring object's value for 'per_subtask' must be in {per_subtask_values},"
                    f"got {scoring['per_subtask']}")

        if not scoring['default_weight'] > 0:
            raise ValueError(
                    f"The scoring default weight must be positive, got {scoring['default_weight']}")

        return scoring

    def _get_statement(self, statement):
        if statement is None or isinstance(statement, str):
            statement = {'base': statement}

        if not isinstance(statement, dict):
            raise TypeError(f"'statement' should be a str or dict, got {type(statement)}")

        if 'base' not in statement:
            raise ValueError("'statement' should have a 'base' key")

        statement.setdefault('compiled',
                statement['base'] if statement['base'] and statement['base'].endswith('.pdf') else None)

        for key in 'base', 'compiled':
            if statement[key]:
                statement[key] = attach_relpath(self.relpath, statement[key])

        if statement['compiled'] and not statement['compiled'].endswith('.pdf'):
            raise ValueError("The compiled statement must be a pdf file")

        return statement

    @property
    def statement_base(self):
        assert 'base' in self.statement
        return self.statement['base']

    @property
    def statement_compiled(self):
        assert 'compiled' in self.statement
        return self.statement['compiled']

    @property
    def scoring_overall(self):
        assert 'overall' in self.scoring
        return self.scoring['overall']

    @property
    def scoring_per_subtask(self):
        assert 'per_subtask' in self.scoring
        return self.scoring['per_subtask']

    @property
    def scoring_default_weight(self):
        assert 'default_weight' in self.scoring
        return self.scoring['default_weight']

    @property
    def logical_scoring(self):
        """ Read-only view of self.scoring that contains only the logical keys for the task type """
        keys = ['overall', 'default_weight'] if self.binary else ['overall', 'per_subtask', 'default_weight']
        return {key: self.scoring[key] for key in keys}

    @property
    def binary(self):
        return not self.valid_subtasks

    def serialize(self):
        raise NotImplementedError # not implemented yet. returns a dict to be json'ed

