<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE. -->
<!-- Edit docs/src/PREPARATION.md instead, then run 'docs/src/makedocs'. -->


This is a detailed guide on how to prepare a problem from scratch using KompGen. 

Actually, not from scratch; this assumes you've already written the problem statement. And also that you've already read the README. 

For a more beginner-friendly tutorial, see [this page](docs/TUTORIAL.md).  



# Introduction  

To prepare a problem, you will write a bunch of different files which will serve different purposes: generators, validators, checkers, etc. We will explain what those are shortly.

Ideally, we will be writing everything in Python 3, although it's possible to use another language for it, or even parts of it; we will learn how to do so later on.


## Some restrictions

Due to limitations in some online judges, we will have some restrictions/requirements in our Python code. Don't worry, there aren't a lot, and they are small. (Other languages are not affected, although that also means you won't be taking full advantage of this library.)

- A notable restriction we have is with importing:

    - Any `import` must be an import star, i.e., of the following form: `from xxx import *`.
    - In addition, the string `### @import` must be appended at the end of it.
    - Builtin packages are exempt and can be imported normally.

- Also, you cannot upload any code you write directly into Polygon. Instead, a command called `kg kompile` is used to generate files that can be uploaded. 

    - In particular, the lines of the form `from xxx import * ### @import` will be replaced by the *whole* code `xxx`. This compresses everything into one file without imports. 

<!-- This also means that obscure bugs may happen due to the fact that the *scopes of the importing and imported modules will become the same*. This doesn't happen in normal usage, but I'm still trying to figure out a long-term solution for this. -->




# Creating a Problem

Run this command:
```bash
$ kg init problem_title
$ kg init problem_title --subtasks 3  # if you have subtasks
```

This will create a folder named `problem_title`. We will write everything related to this problem inside that folder. It will be prepopulated with templates/samples. 



# details.json

The metadata about the problem can be found in `details.json`. It looks like this:

```json
{
    "title": "Find the Sum Extreme",
    "model_solution": ["sol.cpp", "g++ {filename} -o sol.exe", "./sol.exe"],
    "validator": "validator.py",
    "testscript": "testscript",
    "generators": [
        "single_case.py",
        "strong_case.py",
        "edge_case.py",
        "foo_case.cpp"
    ],
    "other_programs": [
        "formatter.py",
        "some_other_code.java"
    ],
    "checker": "checker.py",
    "valid_subtasks": [1, 2, 3],
    "subtasks_files": "subtasks.json",
    "version": "0.2"
}
```

Please update them with the correct values. If your problem doesn't have subtasks, simply remove `valid_subtasks` (or turn it into the empty list).  

The `checker` field may be omitted. It defaults to a simple diff check. There are also a couple of builtin checks: enter `!diff.exact`, `!diff.tokens`, `!diff.real_abs_rel_1e_6`, etc., as the `checker`. (more to come soon...)

Note that the file endings will tell KompGen what language your program is. There will be a predetermined compile and run command for each recognized language. (See `langs.json` for details.) You can also use a three-argument version to specify a file: `[filename, compile, run]`, for example, as used in `model_solution` above. (The two-argument version is `[filename, run]`) For example, if your validator is written in Haskell, then you could write:

```js
    "validator": ["validator.hs", "ghc {filename}", "./{filename_base}"],
```

<!-- Advanced tutorial involves all hidden options here, "extras"/"comments", "subtasks.json", "!diff.*" 

also using {sep}
-->

Now, we can begin writing those files!



# Formatters

This just takes a test case (in a Python representation of your choosing) and prints it to a file in the correct input format. Save it on a file on its own, say `formatter.py`, so you can import it later.

```python
def print_to_file(file, cases):
    print(len(cases), file=file)
    for arr in cases:
        print(len(arr), file=file)
        print(*arr, file=file)
```

This is not strictly required&mdash;indeed, you may remove it altogether from `details.json`&mdash;but is recommended anyway since it is good practice. For example, it makes it easier if you want to change the input/output format; you don't have to update all generators.



# Validators

A validator checks if an input file is strictly valid. It should return with 0 exit code iff the input is valid. A validator should be **strict**: it must not tolerate any extra newline or space. Here's an example:

```python
from sys import *
from kg.validators import * ### @import

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': 1 <= +Var <= 10**5,
    'totaln': +Var <= 5*10**5,
    'a': abs(+Var) <= 10**9,
}

@validator(bounds=bounds)
def validate_file(file, *, lim):

    [t] = file.read.int(lim.t).eoln
    totaln = 0
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln
        totaln += n
        [a] = file.read.ints(n, lim.a).eoln

    [] = file.read.eof
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_file(stdin)
```

Again, note that `### @import` is important. 

Here's a validator that can also check subtasks. It takes the subtask name as the first argument: 

```python
from sys import *
from kg.validators import * ### @import

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': 1 <= +Var <= 10**5,
    'totaln': +Var <= 5*10**5,
    'a': abs(+Var) <= 10**9,
}

subtasks = {
    '1': { 'n': 1 <= +Var <= 10 },
    '2': { 'n': 1 <= +Var <= 1000 },
    '3': { },
}

@validator(bounds=bounds, subtasks=subtasks)
def validate_file(file, subtask=None, *, lim):

    [t] = file.read.int(lim.t).eoln
    totaln = 0
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln
        [a] = file.read.ints(n, lim.a).eoln
        totaln += n

    [] = file.read.eof
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_or_detect_subtasks(validate_file, subtasks, stdin)
```

**Notes:** 

- Use integer literals as subtask names.

- Behind the scenes, `a <= +Var <= b` creates an instance of the `Interval` class, but the custom syntax is more flexible since you can also write something like `a < +Var < b`, and even `(a <= +Var <= b) & (+Var <= c)`.  

- Don't crash or reject if `argv[1]` is not a valid subtask name (or even a valid integer literal); instead, proceed as if you're checking against the largest subtask. (Important for Polygon.)

- The `&` operation is *not* commutative. Always use the subtask `Bounds` as the second argument. (It goes from general to specific.)

- `.int` can also be called like `.int(1, 10**5)`.

- The method names (`.int`, `.space`, etc.) are inspired by testlib (`.read_int`, `.read_space`).

The validators above use **chain-style validation**. Let's say you want to read `x`, `y` and `z` from a line, space-separated, and each with its own constraints. Then instead of writing this, as you would with a testlib-like library:

```python
x = file.read_int(lim.x)
file.read_space()
y = file.read_int(lim.y)
file.read_space()
z = file.read_int(lim.z)
file.read_eoln()
```

you can write it all in one line:

```python
[x, y, z] = file.read.int(lim.x).space.int(lim.y).space.int(lim.z).eoln
```

The chain accepts `int`, `ints`, `token`, `tokens`, `real`, `reals`, `char`, `space`, `eoln`, `eof` and `line`.

I recommend the chain style since it more closely reflects the structure of each line, yet still requires you to exactly specify each byte.

*Note:* The left side of a chain-style assignment must always be enclosed by `[...]`, even if there is only one recipient. Also, `ints` returns a *single* variable (with data type `list`). For example,

```python
[n]    = file.read.int(1, 10**5).space
[x, a] = file.read.int(lim.x).space.ints(n, lim.a).eoln  # here, 'a' is a list
[]     = file.read.eof  # execute a chain without receiving anything
```

*Note on line endings:* Currently, we only support Unix line endings, though this could change in the future. To change the line endings of a file, use `tr -d '\15\32' < windows.txt > unix.txt` for now.  

<!-- TODO Advanced example: graphs, range sum query. -->

<!-- Advanced tutorial involves more details about `read_*` methods, label, GET, WITH_GET, etc. -->


## Detecting subtasks automatically  

If your problem has subtasks, and if your validator handles the subtasks, then we can detect which subtask(s) each input file belongs to by simply running `kg subtasks`. This assumes that `valid_subtasks` and `validator` have been set in `details.json`.  

If your test data are quite big and you find this method slow, then you might want to write a custom subtask detector (as explained in the main README) and place it under `subtask_detector` in `details.json`. 



# Generators

A generator takes some command line arguments and prints a valid test file to the standard output.  

It's easy to write a test generator.  

```python
from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

A = 10**9

def random_cases(rand, *args):
    T, N = map(int, args[:2])
    cases = []
    for cas in range(T):
        n = rand.randint(1, N)
        cases.append([rand.randint(-A, A) for i in range(n)])
    return cases

if __name__ == '__main__':
    write_to_file(print_to_file, random_cases, argv[1:], stdout)
```

**Notes:**

- Don't import `random`. Use the provided random number generator. (It is of type `random.Random`.)

- You can replace `stdout` with a file-like object.

- Obviously, you'll have to work hard to make "strong" test data; for many problems, pure random data like this will not be enough. Writing good tests is beyond the scope of this tutorial.

There are a few more advanced usages and features (will document soon!), but this should cover most use cases.

More detailed tutorials, including the usage of specialized generators (graphs, grids, etc.) can be found [here](GENERATORS.md).  



# Testscript

The testscript file contains instructions on how to generate all the tests. It looks like this:

```bash
# comments are prefixed with hash (#)

! cat sample.in > $
gen_single 10 10 > $
gen_single 10 100 > $
gen_single 10 1000 > $
gen_single 10 10000 > $
gen_multi_lazy 0 10 20 > $
gen_multi_lazy 1 10 20 > $
gen_multi_lazy 2 10 20 > $
gen_multi_lazy 3 10 20 > $
gen_single 10 100000 > $
```

The programs used will be taken from `generators` in `details.json`; in this case, `gen_single.py` and `gen_multi_lazy.py`. They can be in any language.

A `!` at the beginning means "run this bash command as is". Comments begin with `#`. 

This is similar to Polygon's testscript system (although you can't use pipes `|`...yet). In place of `$`, you can write an explicit index, like

```bash
gen_single 10 100000 > 11
```

This will force the output of that line to be the $11$th file. Note that counting starts at $1$, but generated files start at `000`, so this will create `tests/010.in`.  

*Note:* Generators are expected to produce the same output file for the same list of arguments. (The random seed is determined purely by the argument list.) This means that something like this will generate the same files:

```bash
gen_single 10 100000 > $
gen_single 10 100000 > $
gen_single 10 100000 > $
```

If you want to generate different files, pass an extra argument (which will be ignored but will trigger a different random seed) like this:

```bash
gen_single 10 100000 ignored1 > $
gen_single 10 100000 ignored2 > $
gen_single 10 100000 ignored3 > $
```

<!-- Advanced tutorial involves describing the Polygon system, Freemarker (when it's implemented), bracket expansion syntax, etc. -->



# Custom checkers

A checker grades the output of a solution. Most of the time, a `diff` check, comparing the output file and the judge file, is enough, but there are times when a custom checker is needed, e.g., for problems with multiple outputs.

If your problem doesn't require a custom checker, you may skip this section for now and learn it later.

The general template for custom checkers is the following:

```python
from kg.checkers import * ### @import

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    # write your grader here
    
    # Raise this if the answer is incorrect
    raise WA("The contestant's output is incorrect!")
    
    # Raise this if the judge data is incorrect, or if the checking fails for some reason other than WA
    # Any other exception type raised will be considered equivalent to Fail.
    # Any 'Fail' verdict must be investigated since it indicates a problem with the checker/data/etc.
    raise Fail("The judge data is incorrect. Fix it!")

    # the return value is the score, and must be a value between 0.0 and 1.0
    return 1.0 

if __name__ == '__main__': chk()
```

Here, `input_file`, `output_file` and `judge_file` are iterators that enumerate the distinct *lines* of each file. (If you want to enumerate *tokens* instead, pass `"tokens"` to `@set_checker()`. It will be whitespace-insensitive.) `kwargs` will contain other auxiliary data (e.g., test index, source code path, etc.), though it may vary between platforms. Anyway, you probably won't need it most of the time.

Here's an example for the problem "find any longest subsequence of distinct elements":

```python
from kg.checkers import * ### @import

def is_subsequence(a, b):
    ... # code omitted

def get_sequence(file, exc=Exception):
    try:
        m = int(next(file).rstrip())
        b = list(map(int, next(file).rstrip().split(' ')))
    except Exception as e:
        raise ParseError("Failed to get a sequence") from e
    ensure(m >= 0, exc("Invalid length"))
    ensure(len(b) == m, exc(f"Expected {m} numbers but got {len(b)}"))
    return b

def check_valid(a, b, exc=Exception):
    ensure(is_subsequence(a, b), exc("Not a subsequence!"))
    ensure(len(b) == len(set(b)), exc("Values not unique!"))

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    z = int(next(input_file))
    for cas in range(z):
        n = int(next(input_file))
        a = list(map(int, next(input_file).strip().split()))
        if len(a) != n: raise Fail("Judge input invalid")
        cont_b = get_sequence(output_file, exc=WA)
        judge_b = get_sequence(judge_file, exc=Fail)
        check_valid(a, cont_b, exc=WA)
        check_valid(a, judge_b, exc=Fail)
        if len(cont_b) < len(judge_b): raise WA("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

    if output_file.has_next(): raise WA("Extra characters at the end of the output file")
    if judge_file.has_next(): raise Fail("Extra characters at the end of the judge file!")
    return 1.0

if __name__ == '__main__': chk()
```

*Note:* KompGen uses `model_solution` to generate `*.ans` files. But sometimes, you want them to not necessarily contain the answer, but rather just some auxiliary data to help with judging. In this case, you should fill `judge_data_maker` in `details.json`, so it will be used to generate `*.ans` files. 

<!-- TODO graph checking. is_tree, is_connected, etc. -->

<!-- Advanced tutorial involves using the `set_{multi/single}_checker` suite, etc., and also options for `set_checker`.

also, "optimization" via laziness/lambda
-->



# Black magic (advanced)

Feel free to skip this part; it's not needed for most cases. 

There are a few other directives that can be used aside from `### @import`. They can be used to generate specific code for different platforms. (`kg kompile` actually has a builtin preprocessor!)

Perhaps the most useful would be the `@if` directive:

```python
### @@if format == 'hr' {
code_that=only*appears+in_hackerrank
### @@}

line=that_only*appears_in%polygon ### @if format == 'pg'
```

There is also `@replace`, which looks like:

```python
valid_subtasks = None ### @replace None, repr(sorted(details.valid_subtasks))

tmp_filename_base = '/tmp/hr_custom_checker_monika_' ###  @ replace "monika", unique_name()

### @@ replace "range", "xrange" {
for i in range(5):
    print([i*j for j in range(5)])
### @@ }
```

Obviously, Python interprets these as simple comments, but `kg kompile` parses them as directives. This is used to produce the different outputs you see in `kgkompiled`. The expressions themselves are evaluated as Python expressions, with a certain set of available variables. (will document soon)

Try to read `kg/checkers.py` to see the different directives in action. Note that there are other variables accessible aside from `format`. I will document them later. I'd like to clean up this feature first. :)

<!-- Advanced tutorial involves: advanced usages, and other directives like @for. also, usage of compile_lines and stuff (clean it up first). Also show/offer _real_check_gen as example
 -->


## Preprocessor black magic options

The files generated in `kgkompiled` may be too big for your tastes. To make them smaller, there are two (evil) options accepted by `kg kompile` that can reduce the file sizes a bit:

1. `-S`. Attempts to reduce the indentation level; this saves several spaces. Beware, it may break some programs, particularly those with inconsistent indentation. I suggest keeping everything to 4 spaces. 

2. `-C`. A very evil option. See for yourself! :D

Use at your own risk.
