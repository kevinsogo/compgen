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

def write_passwords_format(cont, format_, *, seedval=None, dest='.'):

    if format_ != 'pc2':
        raise PasswordError(f"Unsupported format: {format_}")

    accounts = [(key, account)
            for key in ['leaderboards', 'admins', 'judges', 'teams', 'feeders'] for account in getattr(cont, key)]
    passwords, seed = create_passwords(accounts, seedval=seedval)

    if format_ == 'pc2':
        def get_rows():
            for row in [
                    ('site', 'account', 'displayname', 'password', 'group', 'permdisplay', 'permlogin', 'externalid',
                    'alias', 'permpassword'),
            ]:
                yield row, None

            for idx, scoreboard in enumerate(cont.leaderboards, 1):
                display = scoreboard
                account = f'scoreboard{idx}'
                password = passwords['leaderboards', scoreboard]
                type_ = '[Scoreboard]'
                yield (('1', account, display, password, '', 'false', 'true', str(1000 + idx), '', 'true'),
                        (type_, display, account, password))

            for idx, admin in enumerate(cont.admins, 1):
                display = admin
                account = f'administrator{idx}'
                password = passwords['admins', admin]
                type_ = '[Administrator]'
                yield (('1', account, display, password, '', 'false', 'true', str(1000 + idx), '', 'true'),
                        (type_, display, account, password))

            for idx, judge in enumerate(cont.judges, 1):
                display = 'Judge ' + judge
                account = f'judge{idx}'
                password = passwords['judges', judge]
                type_ = '[Judge]'
                yield (('1', account, display, password, '', 'false', 'true', str(1000 + idx), '', 'false'),
                        (type_, display, account, password))

            for idx, feeder in enumerate(cont.feeders, 1):
                display = feeder
                account = f'feeder{idx}'
                password = passwords['feeders', feeder]
                type_ = '[Feeder]'
                yield (('1', account, display, password, '', 'false', 'true', str(1000 + idx), '', 'true'),
                        (type_, display, account, password))
            
            def team_schools():
                for ts in cont.team_schools:
                    for team in ts['teams']:
                        yield ts['school'], team

            for idx, (school_name, team_name) in enumerate(team_schools(), 1):
                display = team_name
                account = f'team{idx}'
                password = passwords['teams', team_name]
                type_= school_name
                yield (('1', account, display, password, '', 'true', 'true', str(1000 + idx), '', 'false'),
                        (type_, display, account, password))

        rows = []
        passrows = []
        for row, passrow in get_rows():
            rows.append(row)
            if passrow:
                passrows.append(passrow)

        filename = os.path.join(dest, f'accounts_{cont.code}.txt')
        info_print("Writing to", filename, file=stderr)
        with io.open(filename, 'w', encoding='utf-8') as f:
            for row in rows:
                if any(set('\t\n') & set(part) for part in row):
                    raise PasswordError("Only spaces allowed as whitespace in display names.")
                print(u'\t'.join(row), file=f)

    write_passwords(passrows,
            seedval=' or '.join([str(x) for x, g in groupby([seedval, seed]) if x is not None]),
            dest=dest, code=cont.code, title=cont.title)

def write_passwords(accounts, *, dest='.', **context):
    logins = [login for type_, display, login, password in accounts]
    displays = [display for type_, display, login, password in accounts]
    if len(set(logins)) != len(logins): raise PasswordError("Duplicate logins!")
    if len(set(displays)) != len(displays): raise PasswordError("Duplicate display names!")

    def clean_account(account):
        type_, display, login, password = account
        return '' if isinstance(type_, int) else type_, display, login, password

    context.update({
        'per_row': 3,
        'accounts': [clean_account(account) for account in accounts],
    })

    for template in ['table', 'boxes']:
        filename = os.path.join(dest, '_'.join(filter(None, ['logins', context['code'], template])) + '.html')
        info_print("Writing to", filename, file=stderr)
        with open(filename, 'w') as f:
            f.write(
                kg_template_env.get_template(os.path.join('contest_template', f'logins_{template}.html.j2')).render(**context)
            )
