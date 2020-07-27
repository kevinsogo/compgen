from datetime import datetime, timedelta
import json
import os.path
import re

from .utils import *

with open(os.path.join(kg_data_path, 'contest_defaults.json')) as f:
    defaults = json.load(f)

valid_keys = set(defaults) | {"comments", "extras"}

with open(os.path.join(kg_data_path, 'contest_langs.json')) as f:
    langs = json.load(f)

def get_lang(lang):
    if isinstance(lang, str):
        lang = {"lang": lang}
    for key, value in langs.get(lang['lang'], {}).items():
        lang.setdefault(key, value)
    return lang

valid_contestcode = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$')
valid_username = re.compile(r'^[A-Za-z0-9_-]+$')

class ContestDetails(object):
    def __init__(self, details={}, source=None):
        self.details = details
        self.source = source
        self.relpath = os.path.dirname(os.path.abspath(source)) if source is not None else None

        hms_re = re.compile(r'^(?P<h>\d+)\:(?P<m>\d\d)\:(?P<s>\d\d)$')
        def parse_duration(x):
            if isinstance(x, int):
                return timedelta(seconds=x)
            if isinstance(x, dict):
                return timedelta(**x)

            match = hms_re.match(x)
            if match:
                h, m, s = map(int, (match.group(g) for g in 'hms'))
                return timedelta(hours=h, minutes=m, seconds=s)

            raise ValueError(f"Invalid duration: {x!r}")

        def parse_time(x):
            if isinstance(x, int):
                return datetime.utcfromtimestamp(x)
            if isinstance(x, dict):
                return datetime(**x)

            raise ValueError(f"Invalid time: {x!r}")

        # durations
        for key in ['duration', 'scoreboard_freeze_length']:
            setattr(self, key, parse_duration(self.details.get(key, defaults.get(key))))

        # times
        for key in ['start_time']:
            setattr(self, key, parse_time(self.details.get(key, defaults.get(key))))

        # others
        for key in ['title', 'code', 'site_password', 'problems', 'seating', 'seed', 'target_loc',
                'python3_command', 'default_country_code', 'global_statements']:
            setattr(self, key, self.details.get(key, defaults.get(key)))

        # data validation
        if not (self.code and valid_contestcode.match(self.code)):
            raise ValueError(f"Invalid contest code: {self.code!r}")

        for key, long_name in [
                    ('user', 'user'),
                    ('team', 'team'),
                    ('judge', 'judge'),
                    ('admin', 'administrator'),
                    ('leaderboard', 'leaderboard'),
                    ('feeder', 'feeder'),
                ]:
            key_list = key + 's'
            key_count = key + '_count'
            identifier = lambda i: i
            if key_list in self.details:
                if key_count in self.details:
                    raise ValueError(f"{key_list} and {key_count} cannot appear simultaneously")
                value_list = self.details[key_list]
                if isinstance(value_list, str): # open as a possible json file
                    with open(attach_relpath(self.relpath, value_list)) as f:
                        value_list = json.load(f)
                if not isinstance(value_list, list):
                    raise TypeError(f"{key_list} must be a list: got {type(value_list)}")
            else:
                value_count = self.details.get(key_count, defaults.get(key_count))
                if not isinstance(value_count, int):
                    raise TypeError(f"{key_count} must be an int: got {type(value_count)}")
                if value_count < 0:
                    raise ValueError(f"{key_count} must be nonnegative: got {type(value_count)}")
                value_list = [long_name + str(index) for index in range(1, value_count + 1)]

            if key == 'team':
                self.team_schools = self.get_team_schools(value_list)
                value_list = [team for ts in self.team_schools for team in ts['teams']]
                schools = [ts['school'] for ts in self.team_schools]
                for ts in self.team_schools: ts.setdefault('country_code', self.default_country_code)
                if len(set(schools)) != len(schools):
                    raise ValueError("Duplicate school found!")

            if key == 'user':
                self.user_schools = self.get_user_schools(value_list)
                value_list = [user for us in self.user_schools for user in us['users']]
                schools = [us['school'] for us in self.user_schools]
                for us in self.user_schools: us.setdefault('country_code', self.default_country_code)
                if len(set(schools)) != len(schools):
                    raise ValueError("Duplicate school found!")
                identifier = lambda user: user['username']

            if len(set(map(identifier, value_list))) != len(value_list):
                raise ValueError(f"Duplicate {key} found!")

            setattr(self, key_list, value_list)

        # languages
        self.langs = [get_lang(lang) for lang in self.details.get('langs', defaults.get('langs'))]

        # check for extra keys
        for key in self.details:
            if key not in valid_keys:
                raise ValueError(f"Key {key!r} invalid in contest.json. If you wish to add extra data, "
                        "place it under 'comments' or 'extras'")

        super().__init__()

    @classmethod
    def get_team_schools(cls, orig_team_list):
        if not isinstance(orig_team_list, list):
            raise TypeError(f"The team and school data must be a list: got {type(orig_team_list)}")
        team_schools = []
        temp_school = 0
        for team in orig_team_list:
            if isinstance(team, str):
                temp_school += 1
                team = {
                    'school': temp_school,
                    'teams': [team],
                }
            elif not isinstance(team['school'], str):
                raise TypeError(f"School must be a string, got {team['school']!r}")
            team_schools.append(team)

        # attach default values for 'school_short' and 'country_code'
        for team_school in team_schools:
            if 'school_short' not in team_school:
                team_school['school_short'] = shorten_school(team_school['school'])

        return team_schools

    @classmethod
    def get_user_schools(cls, orig_user_list):
        if not isinstance(orig_user_list, list):
            raise TypeError(f"The user and school data must be a list: got {type(orig_user_list)}")

        def is_user_name(obj):
            return isinstance(obj, dict) and (
                set(obj.keys()) == {'first_name', 'last_name', 'username'}
                and (obj['first_name'] or obj['last_name']) # has a name
                and isinstance(obj['username'], str) and valid_username.match(obj['username'])
            )
        user_schools = []
        temp_school = 0
        for user in orig_user_list:
            if isinstance(user, str) or is_user_name(user):
                temp_school += 1
                user = {
                    'school': temp_school,
                    'users': [user],
                }
            elif not isinstance(user['school'], str):
                raise TypeError(f"School must be a string, got {user['school']!r}")
            user_schools.append(user)

        # convert names
        def convert_name(name):
            if isinstance(name, str):
                name = {'first_name': name, 'last_name': None, 'username': name}
            name.setdefault('first_name', None)
            name.setdefault('last_name', None)
            if not is_user_name(name):
                raise TypeError(
                        f"{name!r} cannot be interpreted as a name of a contestant. "
                        f"Note that usernames must match the pattern {valid_username.pattern!r}")
            return name

        for us in user_schools:
            us['users'] = [convert_name(user) for user in us['users']]

        # attach default values for 'school_short' and 'country_code'
        for user_school in user_schools:
            if 'school_short' not in user_school:
                user_school['school_short'] = shorten_school(user_school['school'])

        return user_schools

    @classmethod
    def from_loc(cls, loc):
        with open(loc) as f:
            return cls(json.load(f), source=loc)

    @property
    def end_time(self):
        return self.start_time + self.duration

    @property
    def rel_problems(self):
        return [attach_relpath(self.relpath, prob) for prob in self.problems]

    @property
    def rel_seating(self):
        return attach_relpath(self.relpath, self.seating)

    @property
    def rel_global_statements(self):
        return attach_relpath(self.relpath, self.global_statements)
    

    def serialize(self):
        raise NotImplementedError # not implemented yet. returns a dict to be json'ed


def shorten_school(school):
    ''' best-effort shortening the school name (University of the Philippines --> U Philippines) '''
    # TODO improve this
    if not isinstance(school, str): return ''
    short = ''
    for part in school.split():
        if len(part) < 4: continue
        if part.lower() == 'university': part = 'U'
        if len(short + part) > 20: part = part[:1]
        short += part
    return short[:20] or ' '
