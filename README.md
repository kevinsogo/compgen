# KompGen - A Kompetitib Generator

Use this library if you're one of the following:

- You already have some data, solutions, checkers, etc., already written, and would like to test, run, detect subtasks, convert, etc., locally.
- You want to write a problem from scratch. (Bonus points if you want to write everything in Python.)
- Somewhere in between.

Only works for Ubuntu (and probably some other Unix-based systems) for now. 



# Setup

1. Run `bash setup.sh`. If it prints `DONE`, then it was successful. Make sure you have `python3` and `pip3`.  

    *Note:* Among other things, it installs a bunch of python packages (via `setuptools`). Feel free to modify `setup.sh` if you don't want to install globally, e.g., if you want to use virtualenv or something. 

    If it issues errors for you, please read `setup.sh` and try to find a way to run each line somehow.

2. Add the `scripts/` folder to your `$PATH` variable so you can run the scripts anywhere.

    One way to do this would be to append the line `export PATH="/absolute/path/to/scripts:$PATH"` at the end of `~/.profile`. (Replace `/absolute/path/to/scripts`!) Then the `$PATH` variable will be updated after logging out and then logging in again. (If you can't do that yet, you can run `source ~/.profile` to set it up temporarily.)

3. Whenever this library gets updated (e.g. you pull from the repo), run `bash setup.sh` again to update your installation.



# Useful scripts


## Convert files from one format to another

```bash
$ kg konvert --from polygon path/to/polygon-package --to hackerrank path/to/hr/i-o-folders
$ kg konvert --from hackerrank path/to/hr/i-o-folders --to polygon path/to/polygon-package
```

This keeps the original copy, don't worry.


## Detect subtasks

You have a bunch of files, and you want to know which subtask each one belongs to, automatically. There are two methods, depending on your level of laziness.  

### Method 1: Using a detector script

First, write a program (say `detector.java`) that takes a valid input from stdin and prints the indices of *all* subtasks in which the file is valid. Then run the following:

```bash
$ kg subtasks -i "tests/*.in" -f detector.java
$ kg subtasks -i "tests/*.in" -c java detector # alternative
```

### Method 2: Using a validator which can detect subtasks

Write a program (say `validator.java`) that takes the subtask number as the first argument and an input file from stdin, and exits with code 0 iff the file is valid for that subtask. Then run the following:

```bash
$ kg subtasks -i "tests/*.in" -vf validator.java -s 1 2 3
$ kg subtasks -i "tests/*.in" -vc java validator -s 1 2 3 # alternative
```

Here, `-s` is the list of subtasks. 


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

For the third command, the checker must accept three command line arguments `inputpath outputpath judgepath`. It must exit with code 0 iff the answer is correct. (Currently, `kg test` with a custom checker only supports binary tasks and tasks where each subtask is binary-graded.) 


## Convenience  

Special commands are available if you're using Polygon or HackerRank.

```bash
kg-pg # Polygon
kg-hr # HackerRank
```

This automatically detects the tests based on the corresponding format, so no need to pass `-i` and `-o` arguments. It receives an optional argument `--loc` which says where the test data is located. It defaults to the current folder.


## Generate passwords  

Given a list of teams in JSON format in a file, say, `teams.json`, you can generate passwords for them using:

```bash
kg passwords teams.json
```

This generates the files `kgkompiled/logins_*.html` which contain the same passwords in printable format. (Keep them safe!)

The teams can be grouped by school. See the example in `examples/teams.json`. The school names will be included in the output.

This uses [bootstrap](https://getbootstrap.com/) for styling, so the output would look great with internet access. If you don't have internet access, find [a copy](https://getbootstrap.com/docs/3.3/getting-started/) of `bootstrap.min.css` and place it in the same folder as the `*.html` files.  


## Generate seating arrangements

Given a list of teams in, say, `teams.json`, and the seat layout in, say, `seating.txt`, you can assign seats to them using the following:

```bash
kg seating seating.txt write teams.json > seating.html
```

The teams can be grouped by school. See the example in `examples/teams.json`. This is used so that students from the same school can be placed far from one another.

The format of `seating.txt` is simple. The first grid represents the layout of the seats, and all subsequent grids represent constraints. Higher digits represent stronger constraints. The example in `examples/seating.txt` is a simple layout: 

- It has eight columns, with consecutive columns facing different directions.
- One of the seats, `#`, is unavailable. 
- Each person cannot seat within one position of a schoolmate, and cannot seat within two if at least one is facing the other.

Like the password output, this also uses bootstrap.  



# Full process

You can also prepare a full problem from scratch using this library. Everything can be done locally. If you write it properly, it will be easy to upload it to various judges/platforms.


## Phase A. Preparation

1. Run the following command: `kg init problem_title`. This creates a folder named `problem_title`.

2. Write the following files:

    - [details.json](docs/PREPARATION.md#details.json) (contains metadata)
    - [A formatter](docs/PREPARATION.md#Formatters)
    - [A validator](docs/PREPARATION.md#Validators)
    - [Generators](docs/PREPARATION.md#Generators)
    - [A testscript](docs/PREPARATION.md#Testscript)
    - [A checker](docs/PREPARATION.md#Checkers) (if needed)
    - The model solution


## Phase B. Testing  

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

You can still run `kg make all` if you wish. 


## Phase C. Uploading

1. Run `kg make all` again.  

2. Run `kg kompile`.  

3. Upload the files in `kgkompiled`.  

Behind the scenes, some programs need to be self-contained in a single file before uploading, hence, all imports are "inlined" automatically. A directive called `@import` is used for this. See the longer [tutorial](docs/PREPARATION.md#Some restrictions) for more details.  


## Phase D. Compiling a Contest  

Say you have created a bunch of problems and you would now like to easily upload them to a contest system such as PC2. It is a simple two-step process.

1. Create a `contest.json` file which will contain the details of the contest, including allowed languages and list of problems. A template exists in `examples/templates/contest.json` for you.  

2. Run `kg kontest pc2 path/to/contest.json`. Here, `pc2` indicates the format. For now, only `pc2` is supported, but this may change in the future.  

    In the case of `pc2`, this will create a folder containing (among other things) `contest.yaml`, which can be loaded by PC2. It also contains randomly generated passwords for all accounts.  

More details can be found [here](docs/CONTEST.md), which includes additional things you need to do, like configuring settings that can't be set automatically due to technical limitations (mostly theirs).  



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
*.class
*.executable
*.exe
```

This also means that the folders `tests/` and `kgkompiled/` may be freely deleted if you're trying to free up space. They can always be regenerated from the other files.



# Contributing

- This is quite new so there are probably bugs. Please report the bugs to me so that I can take a look and fix them!

- Feel free to request features/changes/improvements you'd like to see.

- [See this list.](docs/HELP.md) Looking forward to your merge request!


