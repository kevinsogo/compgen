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

# TODO put this into its own file (accounts.py?)
class Account:
    def __init__(self, username, display_name, password, type, index, type_index, *,
                school=None, school_short=None, country_code=None, first_name=None, last_name=None):
        self.username = username
        self.display_name = display_name
        self.password = password
        self.type = type
        assert self.type in {'scoreboard', 'admin', 'judge', 'feeder', 'team', 'user'}
        self.index = index # one-based
        self.type_index = type_index # one-based
        self._school = school
        self._school_short = school_short
        self.country_code = country_code
        self.first_name = first_name
        self.last_name = last_name
        super().__init__()

    @property
    def display_sub(self):
        if self.type == 'scoreboard': return '[Scoreboard]'
        if self.type == 'admin': return '[Administrator]'
        if self.type == 'judge': return '[Judge]'
        if self.type == 'feeder': return '[Feeder]'
        if self.type in {'team', 'user'}: return self.school
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

    def get_pc2_row(self):
        permdisplay = 'true' if self.type == 'team' else 'false'
        permpassword = 'true' if self.type not in {'judge', 'team'} else 'false'
        return ('1', self.username, self.display_name, self.password, '', permpassword,
                'true', self.external_id, '', permpassword)

    def get_dom_row(self):
        # TODO probably rename to "icpc" row, since it follows ICPC standards:
        # https://clics.ecs.baylor.edu/index.php?title=Contest_Control_System_Requirements#teams.tsv
        if self.type == 'team':
            return (self.type_index, self.external_id, 1, self.display_name, self.school,
                    self.school_short, self.country_code)
        else:
            return (self.type, self.display_name, self.username, self.password)
    
    def get_dom_utdata_row(self):
        if self.type == 'team':
            return (self.username, self.password, self.school or ' ', self.school_short or ' ',
                   self.country_code, self.display_name)
        else:
            raise PasswordError("Non-team accounts don't have user_team_data rows.")


def write_passwords_format(cont, format_, *, seedval=None, dest='.'):

    # TODO clean this up

    valid_formats = {'pc2', 'cms-it', 'cms', 'dom'}
    if format_ not in valid_formats:
        raise PasswordError(f"Unsupported format: {format_}")

    accounts = [(key, account)
            for key in ['leaderboards', 'admins', 'judges', 'teams', 'feeders']
            for account in getattr(cont, key)]

    # add users
    accounts += [('users', account['username']) for account in cont.users]

    passwords, seed = create_passwords(accounts, seedval=seedval)

    def _get_account_tuples():
        for idx , scoreboard in enumerate(cont.leaderboards, 1):
            yield dict(display_name=scoreboard,
                       username=f'scoreboard{idx}',
                       password=passwords['leaderboards', scoreboard],
                       type='scoreboard',
                       type_index=idx)

        for idx, admin in enumerate(cont.admins, 1):
            yield dict(display_name=admin,
                       username=f'administrator{idx}',
                       password=passwords['admins', admin],
                       type='admin',
                       type_index=idx)

        for idx, judge in enumerate(cont.judges, 1):
            yield dict(display_name='Judge ' + judge,
                       username=f'judge{idx}',
                       password=passwords['judges', judge],
                       type='judge',
                       type_index=idx)

        for idx, feeder in enumerate(cont.feeders, 1):
            yield dict(display_name=feeder,
                       username=f'feeder{idx}',
                       password=passwords['feeders', feeder],
                       type='feeder',
                       type_index=idx)
        
        team_schools_iter = ((ts, team) for ts in cont.team_schools for team in ts['teams'])
        for idx, (school_data, team_name) in enumerate(team_schools_iter, 1):
            yield dict(display_name=team_name,
                       username=f'team{idx}',
                       password=passwords['teams', team_name],
                       type='team',
                       type_index=idx,
                       school=school_data['school'],
                       school_short=school_data['school_short'],
                       country_code=school_data['country_code'])

        user_schools_iter = ((us, user) for us in cont.user_schools for user in us['users'])
        for idx, (school_data, user_name_data) in enumerate(user_schools_iter, 1):
            display_name = ' '.join(
                    user_name_data[key] for key in ('first_name', 'last_name') if user_name_data.get(key)
                )
            yield dict(display_name=display_name,
                       username=user_name_data.get('username', f'user{idx}'),
                       password=passwords['users', user_name_data['username']],
                       type='user',
                       type_index=idx,
                       school=school_data['school'],
                       school_short=school_data['school_short'],
                       country_code=school_data['country_code'],
                       first_name=user_name_data.get('first_name'),
                       last_name=user_name_data.get('last_name'))

    # reuses the 'accounts' variable so be careful
    accounts = [Account(index=idx, **args) for idx, args in enumerate(_get_account_tuples(), 1)]

    if format_ == 'pc2':
        filename = os.path.join(dest, f'accounts_{cont.code}.txt')
        def get_pc2_rows():
            yield ('site', 'account', 'displayname', 'password', 'group', 'permdisplay', 'permlogin', 'externalid',
                    'alias', 'permpassword')
            yield from (account.get_pc2_row() for account in accounts)
        write_tsv(filename, get_pc2_rows())

    if format_ == 'dom':
        # https://www.domjudge.org/pipermail/domjudge-devel/2015-September/001753.html
        # probably not applicable anymore; if so, feel free to replace "File_Version"
        accounts_dom_rows = {'teams': [['File_Version', 1]], 'accounts': [['File_Version', 1]]}
        dom_groups = {'teams': ['team'], 'accounts': ['judge', 'admin', 'analyst']}
        dom_group = {type: group for group, types in dom_groups.items() for type in types}
        for account in accounts:
            if account.type in dom_group:
                accounts_dom_rows[dom_group[account.type]].append(account.get_dom_row())
        for type_, rows in accounts_dom_rows.items():
            write_tsv(os.path.join(dest, f'{type_}.tsv'), rows)

        dom_utdata_rows = [account.get_dom_utdata_row() for account in accounts if account.type == 'team']
        write_separated_values(os.path.join(dest, 'user_team_data.txt'), dom_utdata_rows, sep=u'\n', disallowed='\t\n')

        # copy the php script (sad, php)
        source = os.path.join(kg_contest_template, 'dom', 'dom_create_teams.php')
        target = os.path.join(dest, 'dom_create_teams')
        copy_file(source, target)
        make_executable(target)

        print()
        warn_print('!!!!!!!!!!')
        warn_print('NOTE: Passwords are not automatically set if you import teams.tsv to DOMjudge!')
        warn_print('Instead, use user_team_data.txt to import the team data (including passwords) directly to the '
                'database by doing the following:')
        print()
        warn_print('1. Copy the files "dom_create_teams" and "user_team_data.txt" into the bin/ folder of your '
                'domserver machine. ')
        warn_print('   (Note: for reference, this folder is found in the domserver Docker container at '
                '/opt/domjudge/domserver/bin/)')
        warn_print('2. Go to the said bin/ folder (in the domserver machine), then run '
                './dom_create_teams < user_team_data.txt')
        print()
        warn_print('!!!!!!!!!!')
        print()

    write_passwords(accounts,
            seedval=' or '.join([str(x) for x, g in groupby([seedval, seed]) if x is not None]),
            dest=dest, code=cont.code, title=cont.title)

    return passwords, accounts


def write_tsv(filename, rows):
    write_separated_values(filename, rows, sep=u'\t', disallowed='\t\n')

def write_csv(filename, rows):
    write_separated_values(filename, rows, sep=u',', disallowed=',\n')

def write_separated_values(filename, rows, *, sep=' ', disallowed=' \n'):
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
        kg_render_template_to(os.path.join(kg_contest_template, f'logins_{template}.html.j2'), filename, **context)
