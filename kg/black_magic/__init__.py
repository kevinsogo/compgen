import re
from sys import stdout, stderr
from random import Random
import base64, zlib

class ParseException(Exception):
    def __init__(self, lineno, message):
        self.lineno = lineno
        self.message = message
        super(ParseException, self).__init__()

valid_open = re.compile(r'\s*###\s*@@(.*){\s*$')
valid_close = re.compile(r'\s*###\s*@@\s*}\s*$')
valid_inline = re.compile(r'(.*)###\s*@([^@].*)$')

command_re = re.compile(r'\s*([-_A-Za-z0-9]+) (.*)$')

CLOSE = '### @@ }'

bads = [
    # generic
    (re.compile(r'###'), "'###' found but couldn't parse. Possible mistake."),
    (re.compile(r'##\s*@'), "'## @' found but couldn't parse. Possible mistake."),
]

import_line = re.compile(r'^(?P<indent>\s*)from\s+(?P<module>[.A-Za-z0-9_]+)\s+import\s*\*\s*$')

def extract_import(line):
    match = import_line.match(line)
    if match: return match['indent'], match['module']
    raise Exception("Unsupported import line: {}".format(line))


def enclose(seq):
    yield from seq
    yield None, CLOSE

class Parsed:
    def __init__(self, command, lines, module_loc):
        self.module_loc = module_loc
        match = command_re.match(command + ' ')
        if match is None: raise Exception("Invalid command: {}".format(command))
        self.command, self.args = command, args = match.groups()
        del command
        self.children = []
        while True:
            try:
                lineno, line = next(lines)
            except StopIteration:
                raise Exception("Consumed all lines before parsing everything. Bracket mismatch.")

            def get_child():
                match = valid_open.match(line)
                if match is not None:
                    command, = match.groups()
                    return Parsed(command, lines, module_loc)
                match = valid_close.match(line)
                if match is not None:
                    return
                match = valid_inline.match(line)
                if match is not None:
                    pline, command = match.groups()
                    return Parsed(command, enclose(enumerate([pline], lineno)), module_loc)

                # try matching bads 
                for bad, message in bads:
                    if bad.search(line):
                        print("WARNING: Line {}. {} ... {}".format(lineno, message, line), file=stderr)
                return line
            child = get_child()
            if child is None: break
            self.children.append(child)
        super(Parsed, self).__init__()

    def pretty_print(self, indent=0, file=stdout):
        tab = '    '
        print(tab*indent, 'COMMAND', repr(self.command), 'ARGS', repr(self.args), sep='', file=file)
        indent += 1
        for child in self.children:
            if isinstance(child, str):
                print(tab*indent, repr(child), sep='', file=file)
            else:
                child.pretty_print(indent, file=file)

    # we're keeping indent as a param. opens up the possibility of handling multilines. but I doubt it.
    def compile(self, context, indent='', begin=True):
        if self.command == 'begin' and begin:
            yield from self.compile_children(context, indent=indent)
        elif self.command == 'if':
            # print('evaluating', self.args)
            if eval(self.args, context):
                yield from self.compile_children(context, indent=indent)
        elif self.command == 'import':
            if self.args.strip(): raise Exception("Unsupported @import args: {}".format(self.args))
            [(wline, line)] = self.compile_children(context, indent=indent)
            nindent, module = extract_import(line)
            yield from context['import'](self, nindent, module, context)
        elif self.command == 'replace':
            # print('evaluating', self.args)
            source, target = map(str, eval(self.args, context))
            for wline, line in self.compile_children(context, indent=indent):
                yield wline, line.replace(source, target)
        elif self.command == 'set':
            print("SETTING", self.args, context['write'])
            exec(self.args, context)
            print("GOT", context['write'])
            [(wline, line)] = self.compile_children(context, indent=indent)
            if line.strip(): raise Exception("Invalid set command. must not enclose!")
        else:
            raise Exception("Unknown directive: {}".format(self.command))

    def compile_children(self, context, indent=''):
        for child in self.children:
            if isinstance(child, str):
                yield context['write'], indent + child
            else:
                yield from child.compile(context, indent=indent, begin=False)

def parse_contents(lines, module_loc):
    elines = enclose(enumerate(lines, 1))
    parsed = Parsed('begin', elines, module_loc)
    try:
        next(elines)
        raise Exception("Parsed only a prefix. Bracket mismatch.")
    except StopIteration:
        return parsed

rand = Random()
def unique_name():
    unique_name.index += 1
    return 'BLACK_MAGIC_' + str(rand.randrange(10**9)) + '_' + str(unique_name.index)
unique_name.index = 0


def import_(parent, indent, module, context):
    module_id = context['get_module_id'](module, context)

    # import once only
    imported = context['imported']
    imported.setdefault(module_id, []).append(module)
    if imported[module_id] != [module]:
        for module_base in imported[module_id]:
            if module_base != module:
                # this requirement is just for sanity, for now.
                raise Exception("Differing import names for module {}: {} and {}. Make sure they are the same.".format(module_id, module_base, module))

    # update 'imported'
    if imported[module_id] != [module]:
        print('skipping duplicate import', module)
        return

    # now, actually import
    print('expanding import of', module)
    lines = context['load_module'](module_id)

    # give __name__ a unique name so the program knows in context that it is being pasted somewhere.
    name = unique_name()
    if context['import_extras']: yield context['write'], indent + '{name}, __name__ = __name__, "{name}"'.format(name=name)
    ncontext = dict(context)
    ncontext['parent'] = parent
    ncontext['parent_context'] = context
    ncontext['current_id'] = module_id
    yield from parse_contents(lines, module_id).compile(ncontext, indent=indent)
    if context['import_extras']: yield context['write'], indent + '__name__ = {name}'.format(name=name)
    if context['import_extras']: yield context['write'], indent + 'del {name}'.format(name=name)


def compile_contents(lines, **context):
    strong_context = {
        'import': import_,
        'parent': None,
        'parent_context': None,
        'imported': {},
        'current_id': None,
        'unique_name': unique_name,
    }
    for key, value in strong_context.items():
        if key in context: raise Exception("Reserved context key: '{}'".format(key))
        context[key] = value

    weak_context = {
        'import_extras': True,
        'write': True,
        'shift_left': False,
        'compress': False,
    }
    for key, value in weak_context.items():
        if key not in context: context[key] = value

    def get_lines():
        for wline, line in parse_contents(lines, None).compile(context):
            if wline:
                if context['shift_left']:
                    tabs = (len(line) - len(line.lstrip(' '))) // 4
                    line = '\t'*tabs + line.lstrip(' ')
                yield line

    if context['compress']:
        x = base64.b64encode(zlib.compress('\n'.join(get_lines()).encode('utf-8')))
        yield "import base64,zlib;exec(zlib.decompress(base64.b64decode({})).decode('utf-8'))".format(repr(x))
    else:
        yield from get_lines()
