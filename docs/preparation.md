<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE. Edit docs_src/preparation.md instead, then run './makedocs'. -->




This is a detailed guide on how to create a problem from scratch using this KompGen. Actually, not from scratch; let's assume you've already written the problem statement.

This also assumes you've already read the README. 




# Introduction  

We will be writing everything ideally in Python 3: generators, validators, checkers, etc. (It's possible to use another language to write some of those parts; we will learn how to do so later ron.)

## Some restrictions

Due to limitations in some of the online judges we're considering, we will have a few restrictions/requirements in our Python code.

- The biggest limitation we have is with importing packages:

    - Any `import`, aside from builtin packages, must be an import star, i.e., of the following form: `from xxx import *`.
    - In addition, these import statements must be *unindented*.
    - The string `### @import` must be appended at the end of it.

- You cannot upload any code you write directly into Polygon. Instead, a command called `kg kompile` is used to generate files that can be uploaded. 

    - In particular, the lines of the form `from xxx import * ### @import` will be replaced by the *whole* code `xxx`. This makes everything into one file without imports. 



# Creating a Problem

Run this command:
```bash
kg init problem_title
```

This will create a folder named `problem_title`. We will write everything related to this problem inside that folder. It will be prepopulated with templates. 


# details.json

The metadata about the problem can be found in `details.json`. It looks like this:

```json
{
    "title": "Addition",
    "model_solution": ["sol.cpp", "g++ sol.cpp -o sol.cpp.executable", "./sol.cpp.executable"],    
    "validator": "validator.py",
    "checker": "checker.py",
    "testscript": "testscript",
    "generators": [
        "single_case.py",
        "multi_case.py",
        "multi_case_lazy.py"
    ],
    "other_programs": [
        "formatter.py"
    ],
    "valid_subtasks": [1, 2, 3],
    "subtasks_files": "subtasks.json"
}
```
Feel free to update it with the correct values. If your problem doesn't have subtasks, simply remove `valid_subtasks` (or make it the empty list). 

Note that the file endings will tell KompGen what language your program is, and there will be a predetermined compile and run command for each recognized language. You can also choose to use the three-argument version `[filename, compile, run]` to specify a file. (The two-argument version is `[filename, run]`) For example, if your validator is written in Haskell, then you write:

```js
    "validator": ["validator.hs", "ghc validator.hs", "./validator"],
```

The `checker` field may be omitted, and defaults to a simple diff check. There are also a couple of builtin checks, just write `!diff.exact`, `!diff.tokens`, or `!diff.real_abs_rel_1e_6`. (more to come soon...)

Now, we can begin writing those files!




# Formatters

This just takes a test case and prints it to a file in the correct input format. Save it on a file on its own, say `formatter.py`, so you can import it later.

```python
def print_to_file(file, cases):
    print(len(cases), file=file)
    for arr in cases:
        print(len(arr), file=file)
        print(*arr, sep=' ', file=file)
```



# Validators

A validator checks if an input file is valid. It should return with 0 exit code iff the input is valid. Validators should be strict: no tolerance for any extra newline or space. Here's an example:

```python
from sys import *
from kg.validators import * ### @import

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
    'a': Interval(-10**9, 10**9),
}

@validator
def validate_file(file):
    lim = Bounds(bounds)

    t = file.read_int(lim.t)
    file.read_eoln()
    totaln = 0
    for cas in xrange(t):
        n = file.read_int(lim.n)
        totaln += n
        file.read_eoln()
        a = []
        for i in xrange(n):
            a.append(file.read_int(lim.a))
            (file.read_space if i < n - 1 else file.read_eoln)()

    file.read_eof()
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    validate_file(stdin)
```

Again, note that `### @import` is important.

Here's a validator that can also check subtasks. It takes the subtask name as an argument: 

```python
from sys import *
from kg.validators import * ### @import

subtasks = {
    '1': {
        'n': Interval(1, 10),
    },
    '2': {
        'n': Interval(1, 1000),
    },
    '3': {
    },
}

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
    'a': Interval(-10**9, 10**9),
}

@validator
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    t = file.read_int_eoln(lim.t)
    totaln = 0
    for cas in range(t):
        n = file.read_int_eoln(lim.n)
        a = file.read_ints_eoln(n, lim.a)
        totaln += n

    file.read_eof()
    ensure(totaln in lim.totaln)

if __name__ == '__main__':
    subtask = argv[1] if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
```

**Notes:** 

- Don't crash or reject if `argv[1]` is not a valid subtask name; instead, proceed as if you're checking against the largest subtask.  

- Use integer literals as subtask names.

- `.read_int` can also be called like `.read_int(1, 10**5)`.


Alternatively, you may use the "chain style" validation. Let's say you want to read `x`, `y` and `z` from a line, space-separated, and each with its own constraints. Then instead of writing this,

```python
x = file.read_int(lim.x)
file.read_space()
y = file.read_int(lim.y)
file.read_space()
z = file.read_int(lim.z)
file.read_eoln()
```

we can write it all in one line:

```python
[x, y, z] = file.read .int(lim.x). space .int(lim.y). space .int(lim.z). eoln
```

The chain accepts `int`, `ints`, `token`, `char`, `space`, `eoln`, and `eof` (and possibly more in the future).

Finally, there is also `read_int_eoln` which is convenience for a `read_int` followed by a `read_eoln`. There's also `read_int_space`, `read_token_eoln`, etc.


## Subtasks  

If your problem has subtasks, and if your validator handles subtasks, then we can detect which subtask(s) each input file belongs to by simply running the following:

```bash
kg subtasks -vf validator.py -s 1 2 3
```

Here, `1 2 3` is the list of subtasks. You may omit the `-vf validator.py` part if `validator.py` is already set in `details.json`.





# Generators

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

- Don't import `random`. Use the provided random number generator.

- You can replace `stdout` with a file-like object.



# Testscript

The test script file contains instructions on how to generate all the tests. It looks like this:

```bash
# comments go here

! cat sample.in > $

single_case 10 10 > $
single_case 10 100 > $
single_case 10 1000 > $
single_case 10 10000 > $
# multi_case [5-8,10] 10 1000 > {5-8,10}
multi_case_lazy 0 10 20 > $
multi_case_lazy 1 10 20 > $
multi_case_lazy 2 10 20 > $
multi_case_lazy 3 10 20 > $
single_case 10 100000 > $
```

This is similar to Polygon's system, though more limited since you have to use `$`, etc. This is a bit limited in expessive power for now, but we'd like to change that soon.






# Custom checkers

The most general template for custom checkers is the following:

```python
from kg.checkers import * ### @import

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    # write your grader here
    
    # Raise this if the answer is incorrect
    raise WA("The contestant's output is incorrect!")
    
    # Raise this if the judge data is incorrect, or if the checking fails for some reason other than WA
    # Any other exception type raised will be considered equivalent to Fail.
    raise Fail("The judge data is incorrect. Fix it!")

    # the return value is the score, and must be a value between 0.0 and 1.0
    return 1.0 

if __name__ == '__main__': chk()
```

Here, `input_file`, `output_file` and `judge_file` are iterators that enumerate the distinct *lines* of each file.

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
        raise ParseError("Failed to get a sequence: " + str(e))
    ensure(m >= 0, "Invalid length", exc=exc)
    ensure(len(b) == m, lambda: "Expected {} numbers but got {}".format(m, len(b)), exc=exc)
    return b

def check_valid(a, b, exc=Exception):
    ensure(is_subsequence(a, b), "Not a subsequence!", exc=exc)
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    z = int(next(input_file))
    for cas in range(z):
        n = int(next(input_file))
        a = list(map(int, next(input_file).strip().split()))
        if len(a) != n:
            raise Fail("Judge input invalid")
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




# Black Magic (advanced)

Feel free to skip this part; it's not needed at all.

There are a few other directives that can be used aside from `### @import`. Perhaps the most useful would be the `@if` directive:

```python
### @@if format == 'hr' {
code_that_only_appears_in_hackerrank
### @@}

line_that_only_appears_in_polygon ### @if format == 'pg'
```
The conditionals are evaluated as Python expressions with a certain set of available variables.

There is also `@replace`, which looks like:

```python
valid_subtasks = None ### @replace None, str(sorted(details.valid_subtasks))

tmp_filename_base = '/tmp/hr_custom_checker_monika_' ### @replace "monika", unique_name()

### @@replace "xrange", "range" {
for i in xrange(5):
    print([i*j for j in xrange(5)])
### @@}
```

Obviously, Python interprets these as simple comments, but `kg kompile` parses them as directives. This is used to produce the different outputs you see in `kgkompiled`. 

Try to read `kg/checkers.py` to see the different directives in action. Note that there are other variables accessible aside from `format`. (will document later...)
