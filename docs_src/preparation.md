

This is a detailed guide on how to prepare a problem from scratch using KompGen. 

Actually, not from scratch; this assumes you've already written the problem statement. And also that you've already read the README. 




# Introduction  

When perparing a problem, you usually write a bunch of different files which serve different purposes: generators, validators, checkers, etc. We will explain what those are shortly.

Ideally, we will be writing everything in Python 3, although it's possible to use another language to write some of those parts; we will learn how to do so later on.



## Some restrictions

Due to limitations in some online judges, we will have some restrictions/requirements in our Python code. Don't worry, there aren't a lot, and they are small. (Other languages are not affected, although that also means you won't be taking full advantage of this library.)

- A notable restriction we have is with importing:

    - Any `import` must be an import star, i.e., of the following form: `from xxx import *`. (Builtin packages are exempt and can be imported normally.)
    - In addition, these import statements must be *unindented*.
    - The string `### @import` must be appended at the end of it.

- Also, you cannot upload any code you write directly into Polygon. Instead, a command called `kg kompile` is used to generate files that can be uploaded. 

    - In particular, the lines of the form `from xxx import * ### @import` will be replaced by the *whole* code `xxx`. This compresses everything into one file without imports. 





# Creating a Problem

Run this command:
```bash
kg init problem_title
```

This will create a folder named `problem_title`. We will write everything related to this problem inside that folder. It will be prepopulated with templates/samples. 




# details.json

The metadata about the problem can be found in `details.json`. It looks like this:

```json
{{ templates/details.json }}
```

Please update them with the correct values. If your problem doesn't have subtasks, simply remove `valid_subtasks` (or turn it into the empty list). 

The `checker` field may be omitted. It defaults to a simple diff check. There are also a couple of builtin checks: enter `!diff.exact`, `!diff.tokens`, `!diff.real_abs_rel_1e_6`, etc., as the `checker`. (more to come soon...)

Note that the file endings will tell KompGen what language your program is. There will be a predetermined compile and run command for each recognized language. You can also use a three-argument version to specify a file: `[filename, compile, run]`. (The two-argument version is `[filename, run]`) For example, if your validator is written in Haskell, then you could write:

```js
    "validator": ["validator.hs", "ghc validator.hs", "./validator"],
```

Now, we can begin writing those files!




# Formatters

This just takes a test case and prints it to a file in the correct input format. Save it on a file on its own, say `formatter.py`, so you can import it later.

```python
{{ addition/formatter.py }}
```



# Validators

A validator checks if an input file is strictly valid. It should return with 0 exit code iff the input is valid. A validator should be strict: it must not tolerate any extra newline or space. Here's an example:

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

- Don't crash or reject if `argv[1]` is not a valid subtask name (or even a valid integer literal); instead, proceed as if you're checking against the largest subtask. (Important for Polygon.)

- `.read_int` can also be called like `.read_int(1, 10**5)`.

- The method names (`read_int`, `read_space`, etc.) are inspired by testlib.


Alternatively, you may use the **chain style validation**. Let's say you want to read `x`, `y` and `z` from a line, space-separated, and each with its own constraints. Then instead of writing this,

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
[x, y, z] = file.read. int(lim.x). space. int(lim.y). space. int(lim.z). eoln
```

The chain accepts `int`, `ints`, `token`, `char`, `space`, `eoln`, and `eof` (and possibly more in the future). I recommend this one since it more closely reflects the structure of each line, yet still requires you to exactly specify each byte.

*Note:* The left side of a chain-style assignment must always be enclosed by `[...]`, even if there is only one recipient. Also, `ints` returns a *single* variable (with data type "list"). For example,

```python
[n]    = file.read. int(1, 10**5). space
[x, a] = file.read. int(lim.x). space. ints(n, lim.a). eoln # here, 'a' is a list
```



<!-- TODO Advanced example: graphs, range sum query -->



## Detecting subtasks automatically  

If your problem has subtasks, and if your validator handles the subtasks, then we can detect which subtask(s) each input file belongs to by simply running `kg subtasks`. This assumes that `valid_subtasks` and `validator` have been set in `details.json`. 





# Generators

A generator takes some command line arguments and prints a valid test file to the standard output.  

It's easy to write a test generator.  

```python
{{ addition/single_case.py }}
```

**Notes:**

- Don't import `random`. Use the provided random number generator.

- You can replace `stdout` with a file-like object.

There are a few more advanced usages and features (will document soon!), but this should cover most use cases.

<!-- TODO Strict multicase, lazy multicase -->



# Testscript

The testscript file contains instructions on how to generate all the tests. It looks like this:

```bash
{{ addition/testscript }}
```

The programs used will be taken from `generators` in `details.json`; in this case, `single_case.py` and `multi_case_lazy.py`. They can be in any language. A `!` at the beginning means "run this bash command as is". Comments begin with `#`. 

This is similar to Polygon's system, though more limited, since you have to use `$`, etc. This is a bit limited in expessive power for now, but we'll change that soon.

<!-- TODO numbering in testscript -->





# Custom checkers

The most general template for custom checkers is the following:

```python
{{ templates/checker_generic_template.py }}
```

Here, `input_file`, `output_file` and `judge_file` are iterators that enumerate the distinct *lines* of each file.

Here's an example for the problem "find any longest subsequence of distinct elements":

```python
{{ templates/checker_generic.py }}
```

<!-- TODO graph checking. is_tree, is_connected, etc. -->




# Black Magic (advanced)

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
valid_subtasks = None ### @replace None, str(sorted(details.valid_subtasks))

tmp_filename_base = '/tmp/hr_custom_checker_monika_' ###  @ replace "monika", unique_name()

### @@ replace "xrange", "range" {
for i in xrange(5):
    print([i*j for j in xrange(5)])
### @@ }
```

Obviously, Python interprets these as simple comments, but `kg kompile` parses them as directives. This is used to produce the different outputs you see in `kgkompiled`. The expressions themselves are evaluated as Python expressions, with a certain set of available variables. (will document soon)

Try to read `kg/checkers.py` to see the different directives in action. Note that there are other variables accessible aside from `format`. I will document them later. I'd like to clean up this feature first. :)




## Preprocessor black magic options

The files generated in `kgkompiled` may be too big for your tastes. To make them smaller, there are two (evil) options accepted by `kg kompile` that can reduce the file sizes a bit:

1. `-S`. Attempts to reduce the indentation level; this saves several spaces. Beware, it may break some programs, particularly those with inconsistent indenting. I suggest keeping everything to 4 spaces. 

2. `-C`. A very evil option. See for yourself! :D

Use at your own risk.
