from enum import Enum

try:
    from enum import auto
except ImportError:
    def auto(): # hacky for pypy3
        auto.val += 1
        return auto.val
    auto.val = 0

from itertools import count
from sys import stdout, stderr
import base64, re, zlib

from ..script.utils import *

from .commands import *
from .exceptions import *

class ParseError(CompileError): ...


class Directive(Enum):
    KEEP = auto() # a ### @keep line
    OPEN = auto() # an opening ### @@ [...] {
    CLOSE = auto() # a closing ### @@ }
    INLINE = auto() # an inline ### @ [...]
    BAD = auto() # definitely bad syntax. we'll issue an error
    COULD_BE_BAD = auto() # we'll issue a warning. this could just be a mistake
    ECHO = auto() # not a directive. just echo

# the processing will be in this order.
SYNTAX_RULES = [
    (re.compile(r'.*###\s*@.*###.*$'), Directive.BAD, "There must be at most one directive in each line"),
    (re.compile(r'^(.*###\s*)@\s*keep (.*)$'), Directive.KEEP, None),
    (re.compile(r'^(.*)###\s*@\s*@(.+){\s*$'), Directive.OPEN, None),
    (re.compile(r'^(.*)###\s*@\s*@\s*}\s*$'), Directive.CLOSE, None),
    (re.compile(r'^(.*)###\s*@\s*([^\s@].*)$'), Directive.INLINE, None),
    (re.compile(r'^.*###\s*@\s*@\s*{\s*$'), Directive.BAD, "An opening directive must have an argument."),
    (re.compile(r'^.*###\s*@\s*@.*}\s*$'), Directive.BAD, "A closing directive cannot have arguments."),
    (re.compile(r'^.*###\s*@\s*@.*$'), Directive.BAD, "A '### @@' line must end with either { or }."),
    (re.compile(r'^.*###\s*@\s*$'), Directive.BAD, "An inline directive must have an argument."),
    (re.compile(r'^.*###.*$'), Directive.COULD_BE_BAD, "'###' found but couldn't parse. Possible mistake."),
    (re.compile(r'^.*##\s*@.*$'), Directive.COULD_BE_BAD, "'## @' found but couldn't parse. Possible mistake."),
    (re.compile(r'.*'), Directive.ECHO, None),
]
def get_directive_type(line):
    for pattern, directive, message in SYNTAX_RULES:
        match = pattern.match(line)
        if match: return pattern, match, directive, message

    assert False, f"Unmatched line by any syntax rule! This shouldn't happen. {line}"

command_re = re.compile(r'\s*([-_A-Za-z0-9]+) (.*)$')

CLOSE = '### @@ }'

def get_command(command):
    match = command_re.match(command + ' ')
    if match is None: raise ValueError(f"Invalid command: {command!r}")
    command_name, args = match.groups()
    if command_name not in COMMANDS: raise ValueError(f"Unknown command name: {command_name!r} ({command!r})")
    res = COMMANDS[command_name](command_name, args)
    return res

def _enclose(seq, value=CLOSE):
    yield from seq
    yield value

class Parsed:
    def __init__(self, command, lines, module_loc, lineno=None):
        self.start_lineno = lineno
        self.module_loc = module_loc

        # compile command
        try:
            self.command = get_command(command)
        except ValueError as exc:
            raise ParseError(module_loc, lineno, "Unable to parse command") from exc
        del command

        # collect children, until closing line (which must exist)
        def get_children():
            nonlocal lineno
            while True:
                try:
                    lineno, line = next(lines)
                except StopIteration as exc:
                    raise ParseError(module_loc, lineno,
                            "Consumed all lines before parsing everything. Bracket mismatch.")

                pattern, match, directive, message = get_directive_type(line)
                # TODO match?
                if directive == Directive.KEEP:
                    left, right = match.groups()
                    yield left + right
                elif directive == Directive.OPEN:
                    prev_line, command = match.groups()
                    if prev_line.strip(): yield prev_line
                    p = Parsed(command, lines, module_loc, lineno=lineno)
                    lineno = p.end_lineno
                    yield p
                elif directive == Directive.CLOSE:
                    prev_line, = match.groups()
                    if prev_line.strip(): yield prev_line
                    return
                elif directive == Directive.INLINE:
                    pline, command = match.groups()
                    p = Parsed(command, enumerate(_enclose([pline]), lineno), module_loc, lineno=lineno)
                    lineno = p.end_lineno
                    yield p
                elif directive == Directive.BAD:
                    raise ParseError(module_loc, lineno, f"{message} ... {line}")
                elif directive == Directive.COULD_BE_BAD:
                    warn_print(f"[{module_loc} line {lineno}] WARNING: {message} ... {line}", file=stderr)
                    yield line
                elif directive == Directive.ECHO:
                    yield line
                else:
                    assert False, f"Unmatched line by any syntax rule! This shouldn't happen. {line}"

        self.children = list(get_children())
        self.end_lineno = lineno
        super().__init__()

    # TODO implement pretty_print again

    def compile(self, context):
        yield from self.command(self, context)

    def compile_children(self, context):
        for child in self.children:
            if isinstance(child, str):
                yield process_context(child, context)
            else:
                yield from child.compile(context)

def parse_lines(lines, module_loc):
    elines = enumerate(_enclose(lines), 1)
    parsed = Parsed('begin', elines, module_loc, lineno=1)
    try:
        lineno, line = next(elines)
        raise ParseError(module_loc, +lineno, "Parsed only a prefix. Bracket mismatch.")
    except StopIteration:
        return parsed

add_context(strong={
        'parse_lines': (lambda context: parse_lines),
    }, weak={
        'write': True,
        'shift_left': False,
        'compress': False,
    }, copy={
        'write',
    })

def compile_lines(lines, **context):
    for key, valuem in strong_context.items():
        if key in context: raise ValueError(f"Reserved context key: '{key}'")
        context[key] = valuem(context)

    for key, valuem in weak_context.items():
        if key not in context: context[key] = valuem(context)


    def get_raw_lines():
        for lcontext, line in parse_lines(lines, context.get('module_id')).compile(context):
            if lcontext['write']:
                if context['shift_left']:
                    tabs = (len(line) - len(line.lstrip(' '))) // 4
                    line = '\t'*tabs + line.lstrip(' ')
                yield line


    uniquify_re = re.compile(r'__BLACK_MAGIC_UNIQUIFY(?:_\d+)+__')
    def get_lines():
        """Replace __BLACK_MAGIC_UNIQUIFY*__ tokens with unique shorter tokens.

        The new token must not be a substring of the code, to avoid conflicts.

        This can be fooled by crazy stuff like eval('__B' + 'M' + '0__'), but
        I think no one should code like that anyway.
        """

        lines = [*get_raw_lines()]
        assert all(isinstance(line, str) for line in lines)

        def all_substrings_shortlex(lines=[*lines]):
            yield ''
            for l in range(1, sum(map(len, lines))):
                for line in lines:
                    for i in range(len(line) - l + 1):
                        yield line[i:i+l]

        all_substrings_shortlex = all_substrings_shortlex()
        subs = set()
        def is_substring(s):
            while True:
                sub = next(all_substrings_shortlex)
                subs.add(sub)
                if len(sub) > len(s): break
            return s in subs

        tokens = (f"BM{i}" for i in count())

        def new_token():
            while True:
                token = next(tokens)
                if not is_substring(token): return token
                info_print("Skipping", token)

        all_reps = {to_rep for line in lines for to_rep in uniquify_re.findall(line)}
        all_reps = {to_rep: new_token() for to_rep in all_reps}
        info_print("Replacing", len(all_reps), "'uniquify tokens'")

        for line in lines:
            for to_rep in {*uniquify_re.findall(line)}:
                line = line.replace(to_rep, all_reps[to_rep])
            yield line

    if context['compress']:
        # don't try this at home!
        enc = base64.b64encode(zlib.compress('\n'.join(get_lines()).encode('utf-8'), level=9))
        return [f"import base64,zlib;exec(zlib.decompress(base64.b64decode({enc!r})).decode('utf-8'))"]
    else:
        return [*get_lines()]
