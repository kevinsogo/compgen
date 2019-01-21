Some useful programs that will help you write data generators, checkers and validators for Polygon and HackerRank (and later on, other judges as well), *in Python*.  

Needs Python 2 for now. This decision is made so that speedup through PyPy is possible. I'll translate to Python 3 when PyPy 3 becomes ready.  

Let's go through the whole process. I promise this will be easy!





# Setup instructions  

```
bash install.sh
```

The last line printed should be `DONE`.  

Also, add the `scripts/` folder to your `$PATH` variable so you can run the scripts anywhere. One way to do this would be to add the following line at the end of `~/.profile`:

```
export PATH="/path/to/compgen/scripts:$PATH"
```

Replace `/path/to/` with the location of the `compgen` folder. Ensure that there is a trailing newline.

Then the `$PATH` variable will be updated after logging out and then logging in again. (You can run `source ~/.profile` if you want to update `$PATH` in your current session.)


**Polygon note:** Import the file `compgen.py` into "resources".  






# Example Problem

{{{statement.md}}}




# Printing a case to a file

Easy enough, doesn't even use this library! But I suggest writing it on a separate file on its own, say `case_formatter.py`, so that it could be imported later.  

```python
{{{case_formatter.py}}}
```

**Polygon note:** Import this into "resources" as well.




# Validating a file


`compgen` contains testlib-like functions for validating a file. You can alternatively just use testlib here, but there are some other reasons to use this library instead:

- So that the generator files below can possibly import the validator.
- So that we can detect subtasks (explained later).  
- So that we don't have to worry about overflow and undefined behavior.  
- So that you use Python and not C++.  
- So that you use Python and not C++.  
- So that you use Python and not C++.  

A validator should stake input from stdin. It should return with 0 exit code iff the input is valid.

Here's an example of a validator:

```python
{{{validator2.py}}}
```

*Note:* Using things like `Interval` and `Bounds` is completely optional; `.read_int` can also be called like `.read_int(1, 10**5)`. However, using `ensure` is recommended. (It is similar to `assert`.)

*Note:* `.read_ints` method coming up in the future!

**Polygon note:** This file can be used as the "validator" in Polygon.  

Here's a validator that can also check subtasks:


```python
{{{validator.py}}}
```

This takes the subtask name as an argument. The `&` operator merges intervals of two `Bounds` objects.






# A test data generator

It's easy to write a test generator.  

```python
{{{single_case.py}}}
```

The random seed will be based on `argv[1:]`.  

*Note:* Don't import `random`! Instead, use the provided random number generator `rand`. This ensures reproducibility.  

**Polygon note:** You can write files like this and use them under "tests". The usage is very similar to generators written with testlib.

You can make it slightly cleaner by using the convenience function `listify`.  

```python
{{{single_case2.py}}}
```

If you want to validate before printing, make the `validate_file` function above importable, then you could replace the last line with this:

```python
    from validator import validate_file
    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout,
            validate=lambda f: validate_file(f, subtask=1))
```

**Polygon note:** This requires uploading `validator.py` into "resources". For the actual validator to use, we can simply write a small program like this:

```python
from validator import validate_file
from sys import stdin, argv
subtask = int(argv[1]) if len(argv) > 1 else None
validate_file(stdin, subtask=subtask)
```




# Generating multiple files simultaneously

Sometimes, you just want to create several kinds of cases without worrying about how to distribute them into different files. Of course, you could generate all cases first, arrange them, then call `write_to_file` multiple times. This works if you're only generating test data locally. But if you're using Polygon, then there's a small problem: Polygon wants each generator to make only one file!

Well, you could still just generate everything and only print a subset of them, but this is still quite slow since you're generating all the cases every time: you might hit Polygon's time limit. What we want is a way to only generate the necessary files without worrying about how to distribute them into files.  

For this, you can use this pattern:

```python
{{{multifile_cases2.py}}}
```

This "lazily" generates all test data and groups them into some number of files, but only prints out the `index`th group.

The function decorated by `new_case` must contain the bulk of work needed to generate that case; that way, the work is not done for cases that will not be needed. Notice that we also need to pass `n` and `x` through it, since we need to capture their values. (should I just use a lazily-evaluated language for this? haha)

`distribute` is responsible for distributing the (ungenerated) cases into files. The `group_into` convenience function makes it easy to split the files into groups of equal size.  

You may optionally choose to generate additional cases in `distribute`. For example, suppose we want to fill in each file with extra cases so that the sum of $N$s becomes exactly $5\cdot 10^5$ (or as close to it as possible). Then we could do something like this:

```python
{{{multifile_cases.py}}}
```

Here, the keyword arg `n=n` passed to `new_case` is what allows us to access `n` in `distribute`, even though the case hasn't been generated yet. In general, the keyword arguments allow you to store any useful info about the ungenerated case if you need them, without needing to generate the case itself.  



# Detecting subtasks  

You have a bunch of files and you want to be saved the trouble of determining which subtask(s) each file belongs to. We can automate the process.  

First, write a custom script that detects the subtask(s) of a file. For example, we can write the following:

```python
{{{detect_subtasks.py}}}
```

It just prints *all* subtasks as separate tokens. If we save this in `detect_subtasks.py`, then we can use it with `python2 detect_subtasks.py`. It will take input from stdin.

Alternatively, if we're lazy, we can use the validator we wrote above and just run it across all subtasks, and print those where it passes. This is a bit slower, but only by a constant (proportional to the number of subtasks). In fact, the script `subtasks_from_validator` automates this for you! We can simply run the following command (supposing the only subtasks are 1, 2 and 3):

```bash
subtasks_from_validator "python2 validator.py" 1 2 3
```

This takes input from stdin, so if needed, use pipe, or add `< file_to_detect_subtasks.in` at the end.

Either way, once you have a command that detects subtasks, you can just loop across all files using `all_files_subtasks`: 

```bash
all_files_subtasks "tests/*.in" [command to detect subtasks]
```

The `"tests/*.in"` argument should match all files you want to extract subtasks for.

For example, using the commands above,

```bash
all_files_subtasks "tests/*.in" python2 detect_subtasks.py
# or
all_files_subtasks "tests/*.in" subtasks_from_validator "python2 validator.py" 1 2 3
```







# Converting to HackerRank format  

Suppose you downloaded a collection of test cases formatted Polygon-style, and you would like to convert it into a format suitable for uploading to HackerRank. I have a ready-made script for you.

```bash
convert_to_hackerrank path/to/tests
```

Here, `path/to/tests` is the tests folder of the Polygon-style package. It contains all test data.

Once this finishes, two folders, `input` and `output`, will be created. (Their contents will be deleted initially.) To upload to HackerRank, simply zip these two together and upload the .zip file.









# Writing directly to HackerRank format  

Although not recommended, if you don't want to use Polygon, you can also generate everything locally using the following:

1. Write a testset script similar to the one in Polygon, but with a small change: you need to use `$$$` for test enumeration instead of `$` or explicit numbers, e.g.

```bash
{{{testset_script_file}}}
```


2. Use the `direct_to_hackerrank` program to interpret this script. This requires a validator and a working solution.

```bash
direct_to_hackerrank testset_script_file "python2 validator.py" "python2 solution.py" 1 2 3
```

This will generate two folders, `input` and `output`. (Their contents will be deleted initially.) The `output` folder will be populated automatically from the provided solution. They will also be validated, and subtasks will be detected. In the example above, `1 2 3` are the subtasks. If you don't provide these arguments, then sit will assume that the task doesn't have subtasks.

**Warning**: Behind the scenes, the testset script will be converted to a bash file with `$$$` replaced by something, and some lines inserted before and after, hence, it is highly recommended to not make syntax errors. I make no guarantees on what could go wrong if it fails!

*Note:* If you just want to generate the test without a validator and/or a working solution, use `echo` as a substitute. As a "validator", it accepts all files as valid. As a "solution", it just prints dummy answer files. e.g.

```bash
direct_to_hackerrank testset_script_file echo echo
```





# Testing a solution locally with files in HackerRank format

You can use the handy `hr` script to test solutions and regenerate the output files in HackerRank format without needing to generate the input files again.

```bash
hr genout python2 solution.py           # to generate output files in output/
hr gen customfolder python2 solution.py # to generate output files in customfolder/
hr test python2 solution.py             # to test against the output files
hr testc python2 solution.py            # same as 'test', but doesn't print the output of diff
hr run python2 solution.py              # to just run a program across all input files
```

Obviously, the solution can be in any language; just replace the command `python2 solution.py` with the actual command to run your solution. (Compile it first if needed!)



# Custom checkers

TODO add support for custom checkers




# Converting to other formats  

This is TODO. Conversion...

TODO  

- CodeChef  
- Kattis  
- PC2  



# Help needed  


**Important**  

- Do something about the fact that Python's `random` module makes no guarantees of reproducibility across implementations and platforms; see [this](https://stackoverflow.com/questions/8786084/reproducibility-of-python-pseudo-random-numbers-across-systems-and-versions).
- Give a better name than "compgen". We can still rename this package while it's early.    

**Others**  

- Implement missing features above. 
- Improve scripts. Possibly look for mistakes. And badly-written parts.
- Improve `StrictStream`. Right now, I'm manually buffering 10^5 characters at a time, but I think there has to be a more idiomatic way to buffer.  
- Write unit tests, possibly.  
- Come up with better naming practices/conventions.