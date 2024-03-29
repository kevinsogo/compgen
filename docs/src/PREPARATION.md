This is a detailed guide on how to prepare a problem from scratch using KompGen. 

Actually, not from scratch; this assumes you've already written the problem statement. And also that you've already read the README. 

For a more beginner-friendly tutorial, see [this page](./TUTORIAL.md).  



# Introduction  

To prepare a problem, you will write a bunch of different files which will serve different purposes: generators, validators, checkers, etc. We will explain what those are shortly.

Ideally, we will be writing everything in Python 3, although it's possible to use other languages for it, or even only for some parts of it; we will learn how to do so later on.


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

```js
{{ templates/details.json }}
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
{{ addition/formatter.py }}
```

This is not strictly required&mdash;indeed, you may remove it altogether from `details.json`&mdash;but is recommended anyway since it is good practice. For example, it makes it easier if you want to change the input/output format; you don't have to update all generators.



# Validators

A validator checks if an input file is strictly valid. It should return with 0 exit code iff the input is valid. A validator should be **strict**: it must not tolerate any extra newline or space. Here's an example:

```python
{{ addition/validator2.py }}
```

Again, note that `### @import` is important. 

Here's a validator that can also check subtasks. It takes the subtask name as the first argument: 

```python
{{ addition/validator.py }}
```

**Notes:** 

- Use integer literals as subtask names.

- Behind the scenes, `a <= +Var <= b` creates something that contains an `Intervals` object, but this syntax is more flexible since you can also write something like `a < +Var < b`, and even `(a <= +Var < b) & (+Var <= c)`.  

- Don't crash or reject if `argv[1]` is not a valid subtask name (or even a valid integer literal); instead, proceed as if you're checking against the largest subtask. (Important for Polygon.)

- Behind the scenes, the dicts containing the constraints are created as `Bounds(bounds)`, and two such objects can be combined via `&`, e.g., `Bounds(bounds) & Bounds(subtasks['1'])`.
    
    - However, `&` operation is *not* commutative. Always use the subtask `Bounds` as the second argument. (It goes from general to specific.)

- `.int` can also be called like `.int(1, 10**5)`.

The validators above use **chain-style validation**. Let's say you want to read `x`, `y` and `z` from a line, space-separated, and each with its own constraints. Then instead of writing something like this:

```python
x = stream.read_int(lim.x)
stream.read_space()
y = stream.read_int(lim.y)
stream.read_space()
z = stream.read_int(lim.z)
stream.read_eoln()
```

you can write it all in one line:

```python
[x, y, z] = stream.read.int(lim.x).space.int(lim.y).space.int(lim.z).eoln
```

The chain accepts `int`, `ints`, `token`, `tokens`, `real`, `reals`, `char`, `space`, `eoln`, `eof` and `line`.

I recommend the chain style since it more closely reflects the structure of each line, yet still requires you to exactly specify each byte.

*Note:* The left side of a chain-style assignment must always be enclosed by `[...]`, even if there is only one recipient. Also, `ints` returns a *single* variable (with data type `list`). For example,

```python
[n]    = stream.read.int(1, 10**5).space
[x, a] = stream.read.int(lim.x).space.ints(n, lim.a).eoln  # here, 'a' is a list
[]     = stream.read.eof  # a chain with an empty result set
```

*Note on line endings:* Currently, line endings are converted to `\n` via Python's "universal newlines" mode, though I'm planning on allowing a `bytes`-based version of the streams in the future. To change the line endings of a file, use `tr -d '\15\32' < windows.txt > unix.txt` for now.  

<!-- TODO Advanced example: graphs, range sum query. -->

<!-- Advanced tutorial involves more details about `read_*` methods, label, GET, WITH_GET, etc. -->


## Detecting subtasks automatically  

If your problem has subtasks, and if your validator handles the subtasks, then we can detect which subtask(s) each input file belongs to by simply running `kg subtasks`. This assumes that `valid_subtasks` and `validator` have been set in `details.json`.  

If your test data are quite big and you find this method slow, then you might want to write a custom subtask detector (as explained in the main README) and place it under `subtask_detector` in `details.json`. 



# Generators

A generator takes some command line arguments and prints a valid test file to the standard output.  

It's easy to write a test generator.  

```python
{{ addition/gen_single.py }}
```

**Notes:**

- Don't import `random`. Use the provided random number generator. (It is an instance of `random.Random`.)

- You can replace `stdout` with a file-like object.

- Obviously, you'll have to work hard to make "strong" test data; for many problems, pure random data like this will not be enough. Writing good tests is beyond the scope of this tutorial.

There are a few more advanced usages and features (will document soon!), but this should cover most use cases.

More detailed tutorials, including the usage of specialized generators (graphs, grids, etc.) can be found [here](GENERATORS.md).  



# Testscript

The testscript file contains instructions on how to generate all the tests. It looks like this:

```bash
{{ templates/testscript }}
```

The programs used will be taken from `generators` in `details.json`; in this case, `gen_single.py` and `gen_multi_lazy.py`. They can be in any language.

A `!` at the beginning means "run this bash command as is". Comments begin with `#`. 

This is similar to Polygon's testscript system (although you can't use pipes `|`...yet). In place of `$`, you can write an explicit index, like

```bash
gen_single 10 100000 > 11
```

This will force the output of that line to be `tests/011.in`. Note that generated files start at `000`, so this is actually the $12$th file. Omitting the `start=0` line (or replacing it with `start=1`) makes the testscript count from `1` instead, but generated files still start at `000`, so the line goes to `tests/010.in`.

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
{{ templates/checker_generic_template.py }}
```

Here, `input_stream`, `output_stream` and `judge_stream` are iterators that enumerate the distinct *lines* of each file. (If you want to enumerate *tokens* instead, pass `"tokens"` to `@set_checker()`. It will be whitespace-insensitive.) `kwargs` will contain other auxiliary data (e.g., test index, source code path, etc.), though it may vary between platforms. Anyway, you probably won't need it most of the time.

Here's an example for the problem "find any longest subsequence of distinct elements":

```python
{{ templates/checker_generic.py }}
```

*Note:* KompGen uses `model_solution` to generate `*.ans` files. But sometimes, you want them to not necessarily contain the answer, but rather just some auxiliary data to help with judging. In this case, you should fill `judge_data_maker` in `details.json`, so it will be used to generate `*.ans` files. 


# Interactors

Interactors (program that interact with the contestant's solution) are also supported. They are useful for tasks with hidden information.

They're implemented very similarly to checkers. The general template for interactors is the following:

```python
{{ templates/interactor_generic_template.py }}
```



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

PLATFORM = 'cms'
PLATFORM = 'local' ### @rem
```
where `@rem` is an abbreviation of `@if False`.

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

1. `-S`. Attempts to reduce the indentation level; this saves several spaces. Beware, it may break some programs, particularly those with inconsistent indentation, and those with multiline strings not passed to `textwrap.dedent`. I suggest keeping everything to 4 spaces.

2. `-C`. A very evil option. See for yourself! :D

Use at your own risk.
