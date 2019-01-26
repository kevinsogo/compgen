
# KompGen - A Kompetitib Generator

Use this library if you're one of the following:

- You already have some data, solutions, checkers, etc., already written, and would like to test, run, convert, detect subtasks, etc., locally.
- You want to write a problem from scratch. (Bonus points if you want to write everything in Python.)
- Somewhere in between.

*Note:* In case you are looking for a very old version, `checkout` the branch `v01`. If you don't know what that is, never mind it.




# Setup

1. Run `bash setup.sh`. When it prints `DONE`, then it was successful.

    *Note:* Among other things, it installs a bunch of python packages. Feel free to modify `setup.sh` if you don't want to install globally, e.g., if you want to use virtualenv or something. 

2. Add the `scripts/` folder to your `$PATH` variable so you can run the scripts anywhere.

    *Note:* One way to do this would be to append the line `export PATH="/absolute/path/to/scripts:$PATH"` at the end of `~/.profile`. (Replace `/absolute/path/to/scripts`!) Then the `$PATH` variable will be updated after logging out and then logging in again. (If you can't do that yet, you can run `source ~/.profile` to set it up temporarily.)

3. Whenever this library gets updated (e.g. you pull from the repo), run `bash setup.sh` again to update your installation.




# Useful scripts

## Convert files from one format to another

```bash
$ kg konvert --from polygon path/to/polygon-package --to hackerrank path/to/hr/i-o-folders
$ kg konvert --from hackerrank path/to/hr/i-o-folders --to polygon path/to/polygon-package
```

This keeps the original copy, don't worry.


## Detect subtasks


### If you have already written a detector script

```bash
$ kg subtasks -i "tests/*.in" -f detector.java
$ kg subtasks -i "tests/*.in" -c java detector # alternative
```

The detector should print out separate tokens denoting *all* the subtasks in which a file is valid.


### If you already have a validator which can detect subtasks
```bash
$ kg subtasks -i "tests/*.in" -vf validator.java -s 1 2 3
$ kg subtasks -i "tests/*.in" -vc java validator -s 1 2 3 # alternative
```

Here, `-s` is the list of subtasks. 

The validator should exit with code 0 iff a file is valid for that subtask.


## Test with local data

```bash
# generate the output from input. The output file names will be inferred from the patterns.
$ kg gen -i "tests/*.in" -o "tests/*.ans" -f sol.java

# test solution against the input and output files.
$ kg test -i "tests/*.in" -o "tests/*.ans" -f other_sol.cpp

# test solution, with custom checker
$ kg test -i "tests/*.in" -o "tests/*.ans" -f other_sol.cpp -jf checker.cpp

# just run the program against the inputs
$ kg run -i "tests/*.in" -f yet_another_sol.java
```

You can also replace `-f [file]` with `-c [command]`.


The checker must accept three command line arguments `inputpath outputpath judgepath`. It returns 0 iff the answer is correct. Currently, `kg test` with a custom checker only supports binary tasks and tasks where each subtask is binary-graded. 


## Convenience  

Special commands are available if you're using Polygon or HackerRank.

```bash
kg-pg # Polygon
kg-hr # HackerRank
```

This automatically detects the tests based on the corresponding format, so no need to pass `-i` and `-o` arguments. It receives an optional argument `--loc` if the data doesn't exist in the current folder.


# Full process

You can also prepare a full problem from scratch using this library. If you write it properly, it will be easy to upload it to various judges/platforms.

## Preparation

1. Run the following command: `kg init problem_title`. This creates a folder named `problem_title`.

2. Write the following files:

    - [details.json](docs/preparation.md#details.json)
    - [A formatter](docs/preparation.md#Formatters)
    - [A validator](docs/preparation.md#Validators)
    - [Generators](docs/preparation.md#Generators)
    - [A testscript](docs/preparation.md#Testscript)
    - [A checker](docs/preparation.md#Checkers) (if needed)
    - The model solution

## Testing  

1. Run `kg make all`. This will generate the input and output files in `tests/`, which you can look at.

2. Adjust/debug until you're happy with your test data. 

Useful commands during this phase:

```bash
# generate the inputs only, no outputs validation and subtasks detection
$ kg make inputs

# generate the inputs and outputs only
$ kg make inputs outputs

# same as the commands described previously, but you don't have to supply -i and -o
$ kg subtasks
$ kg gen
$ kg test -f sol.cpp
$ kg run -f sol.cpp
```

## Uploading

1. Run `kg make all` again.  

2. Run `kg kompile`.  

3. Upload the files in `kgkompiled`.  

Behind the scenes, some programs need to be compressed into one file before uploading, hence, all imports need to be inlined. See the longer [tutorial](docs/preparation.md) for more details about this.



## Adding to a git repo

If you wish to add the problem folder to a version control system but don't want to commit huge test files, you can use the following `.gitignore`:

```
basura*
input/
output/
temp/
__pycache__
*.pyc
kgkompiled/
build/
*.egg-info/
*.egg
tests/
*.executable
```



# Contributing

- Feel free to request features/changes/improvements you'd like to see.

- [See this list.](docs/HELP.md) Looking forward to your merge request!

