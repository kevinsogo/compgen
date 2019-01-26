

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
{{{templates/details.json}}}
```
Feel free to update it with the correct values. If your problem doesn't have subtasks, simply remove `valid_subtasks` (or make it the empty list). 

Note that the file endings will tell KompGen what language your program is, and there will be a predetermined compile and run command for each recognized language. You can also choose to use a three-argument version to specify a file: `[filename, compile, run]` to specify a file. (The two-argument version is `[filename, run]`) For example, if your validator is written in Haskell, then you write:

```js
    "validator": ["validator.hs", "ghc validator.hs", "./validator"],
```

The `checker` field may be omitted, and defaults to a simple diff check. There are also a couple of builtin checks, just enter `!diff.exact`, `!diff.tokens`, or `!diff.real_abs_rel_1e_6`. (more to come soon...)

Now, we can begin writing those files!




# Formatters

This just takes a test case and prints it to a file in the correct input format. Save it on a file on its own, say `formatter.py`, so you can import it later.

```python
{{{addition/formatter.py}}}
```



# Validators

A validator checks if an input file is valid. It should return with 0 exit code iff the input is valid. Validators should be strict: no tolerance for any extra newline or space. Here's an example:

```python
{{{addition/validator2.py}}}
```

Again, note that `### @import` is important.

Here's a validator that can also check subtasks. It takes the subtask name as an argument: 

```python
{{{addition/validator.py}}}
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
kg subtasks
```

This assumes that `valid_subtasks` and `validator` has been set in `details.json`. 





# Generators

It's easy to write a test generator.  

```python
{{{addition/single_case.py}}}
```

**Notes:**

- Don't import `random`. Use the provided random number generator.

- You can replace `stdout` with a file-like object.



# Testscript

The test script file contains instructions on how to generate all the tests. It looks like this:

```bash
{{{addition/testscript}}}
```

The first arguments will be taken from `generators` in `details.json`. 

This is similar to Polygon's system, though more limited since you have to use `$`, etc. This is a bit limited in expessive power for now, but we'd like to change that soon.






# Custom checkers

The most general template for custom checkers is the following:

```python
{{{templates/checker_generic_template.py}}}
```

Here, `input_file`, `output_file` and `judge_file` are iterators that enumerate the distinct *lines* of each file.

Here's an example for the problem "find any longest subsequence of distinct elements":

```python
{{{templates/checker_generic.py}}}
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