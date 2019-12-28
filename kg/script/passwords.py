import io
import os.path
from itertools import groupby
from random import Random, randrange
from sys import stderr
from textwrap import dedent

from .utils import *

class PasswordError(Exception): ...

def get_password_words():
    if get_password_words.words is None:
        with open(os.path.join(kg_data_path, 'password_words.txt')) as f:
            get_password_words.words = [line.strip().upper() for line in f.readlines()]
            assert all(get_password_words.words), "some empty password lines found."
    return get_password_words.words

get_password_words.words = None

def create_passwords(accounts, *, short=False, seedval=None):
    accounts = list(accounts)
    if len(set(accounts)) != len(accounts):
        raise PasswordError("Duplicate accounts!")

    if seedval is None: seedval = randrange(10**18)

    info_print(f"Using seed {seedval}", file=stderr)
    rand = Random(seedval)

    if short:
        PASSWORD_LETTERS = 'ABCDEFGHJKLMNOPRSTUVWXYZ'
        VOWELS = set('AEIOUY')
        def make_chunk():
            while True:
                chunk = ''.join(rand.choice(PASSWORD_LETTERS) for i in range(3))
                if set(chunk) & VOWELS: return chunk

        def make_password():
            return '-'.join(make_chunk() for i in range(4))
    else:
        password_words = get_password_words()
        def make_password():
            return '-'.join(rand.choice(password_words) for i in range(4))

    return {account: make_password() for account in accounts}, seedval

class Account:
    def __init__(self, username, display_name, password, type, index, type_index, *,
                school=None, school_short=None, country_code=None):
        self.username = username
        self.display_name = display_name
        self.password = password
        self.type = type
        assert self.type in {'scoreboard', 'admin', 'judge', 'feeder', 'team'}
        self.index = index # one-based
        self.type_index = type_index # one-based
        self._school = school
        self._school_short = school_short
        self.country_code = country_code
        super().__init__()

    def get_pc2_row(self):
        permdisplay = 'true' if self.type_ == 'team' else 'false'
        permpassword = 'true' if self.type_ not in {'judge', 'team'} else 'false'
        yield ('1', self.username, self.display_name, self.password, '', permpassword,
                'true', self.external_id, '', permpassword)

    @property
    def display_sub(self):
        if self.type == 'scoreboard': return '[Scoreboard]'
        if self.type == 'admin': return '[Administrator]'
        if self.type == 'judge': return '[Judge]'
        if self.type == 'feeder': return '[Feeder]'
        if self.type == 'team': return self.school
        raise Exception

    @property
    def school(self):
        return self._school if self.has_school else ''

    @property
    def school_short(self):
        return self._school_short if self.has_school else ''

    @property
    def has_school(self):
        return isinstance(self._school, str) and self._school
    
    @property
    def external_id(self):
        # TODO check. not sure what this is for, but I guess we should replace '1000'
        # with values distinct per type?
        return 1000 + self.type_index
    

    def get_dom_row(self):
        # TODO probably rename to "icpc" row, since it follows ICPC standards:
        # https://clics.ecs.baylor.edu/index.php?title=Contest_Control_System_Requirements#teams.tsv
        if self.type == 'team':
            return (self.type_index, self.external_id, 1, self.display_name, self.school,
                    self.school_short, self.country_code)
        else:
            return (self.type, self.display_name, self.username, self.password)


def write_passwords_format(cont, format_, *, seedval=None, dest='.'):

    # TODO clean this up

    valid_formats = {'pc2', 'cms-it', 'dom'}
    if format_ not in valid_formats:
        raise PasswordError(f"Unsupported format: {format_}")

    accounts = [(key, account)
            for key in ['leaderboards', 'admins', 'judges', 'teams', 'feeders'] for account in getattr(cont, key)]
    passwords, seed = create_passwords(accounts, seedval=seedval)

    def get_accounts():
        oidx = 0
        for idx , scoreboard in enumerate(cont.leaderboards, 1):
            oidx += 1
            yield Account(
                display_name=scoreboard,
                username=f'scoreboard{idx}',
                password=passwords['leaderboards', scoreboard],
                type='scoreboard',
                index=oidx,
                type_index=idx)

        for idx, admin in enumerate(cont.admins, 1):
            oidx += 1
            yield Account(
                display_name=admin,
                username=f'administrator{idx}',
                password=passwords['admins', admin],
                type='admin',
                index=oidx,
                type_index=idx)

        for idx, judge in enumerate(cont.judges, 1):
            oidx += 1
            yield Account(
                display_name='Judge ' + judge,
                username=f'judge{idx}',
                password=passwords['judges', judge],
                type='judge',
                index=oidx,
                type_index=idx)

        for idx, feeder in enumerate(cont.feeders, 1):
            oidx += 1
            yield Account(
                display_name=feeder,
                username=f'feeder{idx}',
                password=passwords['feeders', feeder],
                type='feeder',
                index=oidx,
                type_index=idx)
        
        def team_schools():
            for ts in cont.team_schools:
                for team in ts['teams']:
                    yield ts, team

        for idx, (school_data, team_name) in enumerate(team_schools(), 1):
            oidx += 1
            yield Account(
                display_name=team_name,
                username=f'team{idx}',
                password=passwords['teams', team_name],
                type='team',
                index=oidx,
                type_index=idx,
                school=school_data['school'],
                school_short=school_data['school_short'],
                country_code=school_data['country_code'])

    accounts = list(get_accounts()) # reuses the 'accounts' variable so be careful

    if format_ == 'pc2':
        filename = os.path.join(dest, f'accounts_{cont.code}.txt')
        def get_pc2_rows():
            yield ('site', 'account', 'displayname', 'password', 'group', 'permdisplay', 'permlogin', 'externalid',
                    'alias', 'permpassword')
            for account in accounts:
                yield account.get_pc2_row()
        _write_tsv(filename, get_pc2_rows())

    if format_ == 'dom':
        # https://www.domjudge.org/pipermail/domjudge-devel/2015-September/001753.html
        accounts_dom_rows = {'teams': [['File_Version', 1]], 'accounts': [['File_Version', 1]]}
        dom_groups = {'teams': ['team'], 'accounts': ['judge', 'admin', 'analyst']}
        dom_group = {type_: group for group, types in dom_groups.items() for type_ in types}
        for account in accounts:
            if account.type in dom_group:
                accounts_dom_rows[dom_group[account.type]].append(account.get_dom_row())
        for type_, rows in accounts_dom_rows.items():
            _write_tsv(os.path.join(dest, f'{type_}.tsv'), rows)

        def get_user_team_data_rows():
            for account in accounts:
                if account.type == 'team':
                    yield (
                            account.username,
                            account.password,
                            account.school or ' ',
                            account.school_short or ' ',
                            account.country_code,
                            account.display_name)

        _write_separated(os.path.join(dest, 'user_team_data.txt'), get_user_team_data_rows(), sep=u'\n', disallowed='\t\n')

        print()
        warn_print('NOTE: Passwords are not automatically set if you import teams.tsv to DOMjudge!')
        info_print('Instead, use user_team_data.txt to directly import the team data (including passwords) to the '
                'database by doing the following:')
        info_print('1. Copy user_team_data.txt into your domserver machine.')
        info_print('2. Copy the kg/data/dom_create_teams.php file into the bin/ folder of your domserver machine. '
                '(Note: this folder is found in the docker container at /opt/domjudge/domserver/bin/)')
        info_print('3. Run chmod +x dom_create_teams.php (in your domserver machine).')
        info_print('4. Run ./dom_create_teams.php < path/to/user_team_data.txt (in your domserver machine).')
        print()

    write_passwords(accounts,
            seedval=' or '.join([str(x) for x, g in groupby([seedval, seed]) if x is not None]),
            dest=dest, code=cont.code, title=cont.title)

    return passwords


def _write_tsv(filename, rows):
    _write_separated(filename, rows, sep=u'\t', disallowed='\t\n')

def _write_csv(filename, rows):
    _write_separated(filename, rows, sep=u',', disallowed=',\n')

def _write_separated(filename, rows, *, sep=' ', disallowed=' \n'):
    info_print("Writing to", filename, file=stderr)
    with io.open(filename, 'w', encoding='utf-8') as f:
        for row in rows:
            if any(set(disallowed) & set(str(part)) for part in row):
                raise PasswordError(f"Illegal characters found in row {row!r}.")
            print(*row, sep=sep, file=f)


def write_passwords(accounts, *, dest='.', **context):
    # user-side password files [read-only]
    logins = [account.username for account in accounts]
    displays = [account.display_name for account in accounts]
    if len(set(logins)) != len(logins): raise PasswordError("Duplicate logins!")
    if len(set(displays)) != len(displays): raise PasswordError("Duplicate display names!")

    context.update({
        'per_row': 3,
        'accounts': accounts,
    })

    for template in ['table', 'boxes']:
        filename = os.path.join(dest, '_'.join(filter(None, ['logins', context['code'], template])) + '.html')
        info_print("Writing to", filename, file=stderr)
        with open(filename, 'w') as f:
            f.write(
                kg_template_env.get_template(os.path.join('contest_template', f'logins_{template}.html.j2')).render(**context)
            )
