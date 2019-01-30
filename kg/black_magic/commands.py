from random import Random
import functools
import re


from .exceptions import *


class CommandException(CompileException): ...

class EvalException(CommandException): ...



rand = Random()
def make_unique_name(seed=None):
    if seed is None: seed = rand.getrandbits(32)
    rd = Random(seed)
    def unique_name():
        unique_name.index += 1
        return 'BLACK_MAGIC_' + str(rd.randrange(10**9)) + '_' + str(unique_name.index)
    unique_name.index = 0
    return unique_name




def _realize(f, context):
    try:
        return f(context)
    except TypeError:
        return f

COMMANDS = {}

strong_context = {}
weak_context = {}
copy_context = set()

def add_context(strong={}, weak={}, copy=set()):
    for key, value in strong.items():
        if key in strong_context: raise ValueError("Duplicate key in strong_context: {}".format(key))
        strong_context[key] = functools.partial(_realize, value)
    for key, value in weak.items():
        if key in weak_context: raise ValueError("Duplicate key in weak_context: {}".format(key))
        weak_context[key] = functools.partial(_realize, value)
    for key in copy:
        if key in copy_context: raise ValueError("Duplicate key in copy_context: {}".format(key))
        copy_context.add(key)

add_context(weak={'indent': ''})

def set_command(name, strong={}, weak={}):
    add_context(strong=strong, weak=weak)
    def _set_command(Command):
        assert name not in COMMANDS
        COMMANDS[name] = Command
        return Command
    return _set_command

def make_copy_context(context):
    return {key: value for key, value in context.items() if key in copy_context}

# TODO push 'indent' to copy_context and add "post_processors". we now have two:
# "write" post_processor and "indent" post_processor
def process_context(line, context):
    return make_copy_context(context), context['indent'] + line


def try_run(expr, parsed, command, context):
    try:
        return command(expr, context)
    except Exception as exc:
        raise EvalException.for_parsed(parsed, "An exception occurred while running {} via {}: {}".format(repr(expr), command.__name__, str(exc))) from exc


class Command:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        super(Command, self).__init__()

    def expect(self, parsed, ct, lines):
        if ct < 0: raise ValueError("Invalid count to expect: {}".format(ct))
        found = 0
        for wline, line in lines:
            if line.strip():
                found += 1
                if found > ct: raise CompileException.for_parsed(parsed, "Expected {} line(s) but found more inside @{}".format(ct, self.name))
                yield wline, line
        if found < ct: raise CompileException.for_parsed(parsed, "Expected {} line(s) but found {} inside @{}".format(ct, found, self.name))


@set_command('begin', strong={'begin': True})
class Begin(Command):
    def __call__(self, parsed, context):
        # special: only matches the start of a file.
        if context['begin']:
            context['begin'] = False
            yield from parsed.compile_children(context)
        else:
            raise CommandException.for_parsed(parsed, "Cannot 'begin' if not in the beginning of the file")


@set_command('if')
class If(Command):
    def __call__(self, parsed, context):
        # evaluate an expression and write the children if True (or truthy)
        # print('@if: evaluating', repr(self.args))
        if try_run(self.args, parsed, eval, context):
            yield from parsed.compile_children(context)


@set_command('for')
class For(Command):
    def __call__(self, parsed, context):
        # write an expression multiple times.
        try:
            index = self.args.find(' in ')
        except ValueError as exc:
            raise CommandException.for_parsed(parsed, "Cannot parse @for: ' in ' not found!") from exc
        to_assign = self.args[:index].strip()
        is_tuple = ',' in to_assign
        labels = [label.strip() for label in to_assign.split(',')]
        if labels[-1] == '': labels.pop()
        if not labels: raise CommandException.for_parsed(parsed, "Invalid left-side assignment for @for: empty")
        if not all(labels): raise CommandException.for_parsed(parsed, "Invalid left-side assignment for @for: blank labels")

        expr = self.args[index + 4:]
        # print('@for: evaluating', repr(expr))
        for value in try_run(expr, parsed, eval, context):
            if not is_tuple: value = [value]
            if len(labels) != len(value): raise EvalException.for_parsed(parsed, "Invalid assignment for @for: differing lengths: left {} vs right {}".format(len(labels), len(value)))
            for label, val in zip(labels, value):
                context[label] = val
            yield from parsed.compile_children(context)


@set_command('while')
class While(Command):
    def __call__(self, parsed, context):
        # write an expression multiple times.
        # print('@while: evaluating', repr(self.args))
        while try_run(self.args, parsed, eval, context):
            yield from parsed.compile_children(context)


@set_command('replace')
class Replace(Command):
    def __call__(self, parsed, context):
        # replace text in every line inside.
        # print('@replace: evaluating', repr(self.args))
        source, target = map(str, try_run(self.args, parsed, eval, context))
        for wline, line in parsed.compile_children(context):
            yield wline, line.replace(source, target)


@set_command('set')
class Set(Command):
    def __call__(self, parsed, context):
        # set a variable inside the current context.
        # Note that the parent context (from the importing file) is unaffected.
        # print('@set: executing', repr(self.args))
        try_run(self.args, parsed, exec, context)
        [] = self.expect(parsed, 0, parsed.compile_children(context))
        return []


@set_command('import',
        strong={
            'import': (lambda context: _import),
            'parent': None,
            'parent_context': None,
            'imported': (lambda context: {}),
            'unique_name': (lambda context: make_unique_name(context.get('seed'))),
            'current_unique': None,
        }, weak={
            'module_id': None,
            'import_extras': True,
        })
class Import(Command):
    def __call__(self, parsed, context):
        # import a file recursively.
        if self.args.strip(): raise CommandException.for_parsed(parsed, "Unsupported @import args: {}".format(self.args))
        [(wline, line)] = self.expect(parsed, 1, parsed.compile_children(context))
        import_extracted = extract_import(line)
        if not import_extracted: raise CommandException.for_parsed(parsed, "Unsupported import line: {}".format(line))
        nindent, module = import_extracted
        yield from context['import'](parsed, nindent, module, context)

import_line = re.compile(r'^(?P<indent>\s*)from\s+(?P<module>[.A-Za-z0-9_]+)\s+import\s*\*\s*$')

def extract_import(line):
    match = import_line.match(line)
    if match: return match['indent'], match['module']

def _import(parent, indent, module, context):
    module_id = context['get_module_id'](module, context)

    # import once only
    imported = context['imported']
    imported.setdefault(module_id, []).append(module)

    # update 'imported'
    if imported[module_id] != [module]:
        print('skipping duplicate import', module)
        return

    # now, actually import
    print('expanding import of {} (interpreted as module {})'.format(module, module_id))
    lines = context['load_module'](module_id)

    # give __name__ a unique name so the program knows in context that it is being pasted somewhere.
    name = context['unique_name']()
    ncontext = dict(context)
    ncontext.update({
        'indent': indent,
        'parent': parent,
        'parent_context': context,
        'module_id': module_id,
        'current_unique': name,
        'begin': True,
    })

    # recurse to import file
    import_extras = context['import_extras']
    yield process_context("# BLACK_MAGIC start import {}".format(module), ncontext)
    if import_extras: yield process_context('{name}, __name__ = __name__, "{name}"'.format(name=name), ncontext)
    yield from context['parse_lines'](lines, module_id).compile(ncontext)
    if import_extras: yield process_context('__name__ = {name}'.format(name=name), ncontext)
    if import_extras: yield process_context('del {name}'.format(name=name), ncontext)
    yield process_context("# BLACK_MAGIC end import {}".format(module), ncontext)
