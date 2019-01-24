Some useful programs that will help you write data generators, checkers and validators for Polygon and HackerRank (and later on, other judges as well), *in Python*.  

Needs Python 2 for now. This decision is made so that speedup through PyPy is possible. I'll translate to Python 3 when PyPy 3 becomes ready.  



# Setup 

1. Run `bash install.sh`. If should print `DONE` at the end. This sets up most of it.

2. Add the `scripts/` folder to your `$PATH` variable so you can run the scripts anywhere. One way to do this would be to add the line `export PATH="/path/to/compgen/scripts:$PATH"` at the end of `~/.profile`. Then the `$PATH` variable will be updated after logging out and then logging in again. (If you can't do that yet, you can run `source ~/.profile` to set it up temporarily.)

3. Whenever this library gets updated (e.g. you pull from the repo), run `bash install.sh` again to update your installation.



**Notes:**  

- The path containing `compgen` AND the location you're working on shouldn't have spaces and other special characters in it.

- Please don't run multiple scripts simultaneously.



**If you want to use this for Polygon, you need to follow these rules:**

- Any `import`, aside from builtin packages, must be of the following form: `from xxx import *`. In addition, these import statements must be unindented.

- Don't print anything to stderr for validators and generators. Polygon will interpret it as an error.

- But if you're printing something anyway, add the line `from __future__ import print_function` at the beginning of your code, and don't import anything else from `__future__`.  

- You cannot upload any code you write directly into Polygon. Instead, run `polygonate` first, and use the files uploaded inside the created folder `polygon_ready`.  



# Formatters

This just takes a test case and prints it to a file in the correct input format. Save it on a file on its own, say `formatter.py`, so you can import it later.

```python
{{{addition/formatter.py}}}
```



# Validators

A validator checks if an input file is valid. It should return with 0 exit code iff the input is valid. Validators should be strict: no tolerance for any extra newline or space. Here's an example:

```python
{{{templates/validator2.py}}}
```

Here's a validator that can also check subtasks. It takes the subtask name as an argument: 

```python
{{{templates/validator.py}}}
```

**Notes:** 

- Don't crash or reject if `argv[1]` is not a valid subtask name; instead, proceed as if you're checking against the largest subtask.  

- Use integer literals as subtask names.

- `.read_int` can also be called like `.read_int(1, 10**5)`.



# Generators

It's easy to write a test generator.  

```python
{{{addition/single_case.py}}}
```

**Notes:**

- Don't import `random`. Use the provided random number generator.

- You can replace `stdout` with a file-like object.



# Subtasks  

If your problem has subtasks, and if your validator handles subtasks, then we can detect which subtask(s) each input file belongs to by simply running the following:

```bash
subtasks_from_validator 1,2,3 python2 validator.py < input_file
```

Here, `1,2,3` is the list of subtasks, and the remaining arguments represent the validator command.  

To do this across all files, just run:

```bash
all_files_subtasks "tests/*.in" subtasks_from_validator 1,2,3 python2 validator.py
```



# Custom checkers

The most general template for custom checkers is the following:

```python
{{{templates/checker_generic_template.py}}}
```

Here, `input_file`, `output_file` and `judge_file` are iterators that enumerate the distinct *lines* of each file.

**Follow these instructions to make it work for all platforms:** 

- The import line has to be exactly `from compgen.checkers import *`.

- You *must* write the exact same future import statement as in this example.

Here's an example for the problem "find any longest subsequence of distinct elements":

```python
{{{templates/checker_generic.py}}}
```

**Note:** You can't immediately upload checker files. Here's what to do:

- For **Polygon**: Just run `polygonate`; checkers will be included.

- For **HackerRank**: Run `hrate`, then use the files in the folder `hr_ready`. If you need the checker to handle subtasks, run `make_details` first before running `hrate`. It takes the same arguments as `all_files_subtasks`. All this is also automatically created by `direct_to_hackerrank`, as described below.  




# Converting to HackerRank format  

You can convert a collection of test cases formatted Polygon-style to HackerRank-style using:

```bash
convert_to_hackerrank path/to/polygon-package/tests
```

Zip the two resulting folders `input` and `output` together and upload.  



# Writing directly to HackerRank format  

Although not recommended, if you don't want to use Polygon, you can also generate everything locally using the following:

1. Write a testset script similar to the one in Polygon, but in bash, and with a small change: you need to use `$$$` for test enumeration instead of `$` or explicit numbers, e.g.

```bash
{{{addition/testset_script_file}}}
```

2. Use the `direct_to_hackerrank` program to interpret this script. This requires a validator and a working solution.

```bash
direct_to_hackerrank testset_script_file "python2 validator.py" "python2 solution.py" 1,2,3
```

The generated data will be in `input` and `output` and will be validated, and subtasks will be detected and written in `details.json`. In the example above, `1,2,3` are the subtasks. If you don't provide these arguments, then it will assume that the task doesn't have subtasks.

**Warning**: Behind the scenes, the testset script will be *hackily* converted to a bash file (with some bash commands inserted), so **please keep your script simple**.



# Testing a solution locally with files in HackerRank format

You can use the handy `hr` script to test solutions and regenerate the output files in HackerRank format without needing to generate the input files again.

```bash
hr genout python2 solution.py           # to generate output files in output/
hr gen customfolder python2 solution.py # to generate output files in customfolder/
hr test python2 solution.py             # to test against the output files
hr testc python2 solution.py            # same as 'test', but doesn't print the output of diff
hr run python2 solution.py              # to just run a program across all input files
```

The solution can be in any language; just replace the command `python2 solution.py` with the actual command to run your solution.



# Converting to other formats  

TODO  

- CodeChef  
- Kattis  
- PC2  



# Help needed  

- Feel free to request features/changes/improvements you'd like to see.

- [See this list.](docs/HELP.md) Looking forward to your merge request!

