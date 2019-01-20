Some useful programs that will help you write data generators, checkers and validators for polygon and hackerrank.

Needs Python 2 for now. This decision is taken so that speedup through PyPy is possible. I'll translate to Python 3 if PyPy 3 becomes ready.




# Example Problem

Given an array, print the sum of its elements.

The input format is as follows.
    
    T
    N
    A1 A2 ... AN
    N
    A1 A2 ... AN
    ...
    N
    A1 A2 ... AN






# Printing a case to a file

Write this in some file, say `case_formatter.py`, where it could be imported.  

```
from __future__ import print_function

def print_to_file(file, cases):
    print(len(cases), file=file)
    for arr in cases:
        print(len(arr), file=file)
        print(*arr, sep=' ', file=file)
```






# Validating a file


`compgen` contains `testlib`-like functions for validating a file. One can alternatively just use testlib here, but there are some other reasons to use this library instead:

- So that the generator files below can possibly import the validator.
- So that we can test for subtasks.  
- So that we don't have to worry about overflow and undefined behavior.  



No subtasks:


```
from compgen import Interval, Task, validator, ensure

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
    'a': Interval(-10**9, 10**9),
}

@validator
def validate_file(file):
    lim = Task(bounds)

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
    from sys import stdin
    validate_file(stdin)
```

Note that using `Task` is completely optional. `.read_int` can also be called like this: `file.read_int(1, 10**5)`.  

Note: `.read_ints` method coming up in the future!


With subtasks:


```
from compgen import Interval, Task, validator, ensure

subtasks = {
    1: {
        'n': Interval(1, 10),
    },
    2: {
        'n': Interval(1, 1000),
    },
    3: {
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
    lim = Task(bounds) & Task(subtasks.get(subtask))

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
    from sys import stdin, argv
    subtask = int(argv[1]) if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
```

The `&` operator merges intervals of two `Task` objects.






# A test data generator

```
import compgen

A = 10**9

def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    cases = []
    for cas in xrange(T):
        n = rand.randint(1, N)
        cases.append([rand.randint(-A, A) for i in xrange(n)])
    return cases

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout)
```

The random seed will be based on `argv[1:]`.

One can make it slightly cleaner by using the convenience function `listify`.  

```
import compgen

A = 10**9

@compgen.listify
def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    for cas in xrange(T):
        n = rand.randint(1, N)
        yield [rand.randint(-A, A) for i in xrange(n)]

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout)
```


If you want to validate before printing, make the `validate_file` function above importable, then you could replace the last line inside `if __name__ == '__main__':` with this this:

```
    from validator import validate_file # import the validate_file function
    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout, validate=lambda f: validate_file(f, subtask=1))
```





# Generating multiple files simultaneously

Sometimes, you just want to create several kinds of cases without worrying about how to distribute them into different files. Of course, you could generate all cases first, arranging them, then calling `write_to_file` multiple times. This works if you're only generating locally. But this has a downside: Polygon wants each generator to make only one file. One could just ignore the rest of the files, but this is still quite slow since you're generating all the cases every time. What we want is a way to only generate the necessary files without worrying about distributing into files.  

You can use this pattern:

```
import compgen

A = 10**9
def make_case(rand, n):
    return [rand.randint(-A, A) for i in xrange(n)]

def many_cases(rand, new_case, *args):
    ''' generates multiple cases that will be distributed to multiple files '''
    T, N = map(int, args[:2])
    for n in [1, N/10, N/2, 9*N/10, N]:
        for x in xrange(8):
            # generate a case where all numbers are == x mod 8
            @new_case(n, x)
            def make_case(rand, n, x):
                return [rand.randrange(-A + (x + A) % 8, A+1, 8) for i in xrange(n)]

    while new_case.total_cases % T:
        new_case(N)(make_case)


def distribute(rand, new_case, casemakers, *args):
    T, N = map(int, args[:2])
    return compgen.group_into(T, rand.shuff(casemakers)) # shuffle and then divide into groups of size T

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_nth_group_to_file(int(argv[1]), print_to_file, many_cases, distribute, argv[2:], stdout)
```


The function decorated by `new_case` must contain the bulk of work needed to generate that case; that way, the work is not done for cases that will not be needed. One also needs to pass `n` and `x` through it to capture their values.

(should I just use a lazily-evaluated language for this? haha)

`distribute` is responsible for distributing the (ungenerated) cases into files. One can choose to generate additional cases here. For example, suppose we want to fill in each file with extra cases so that total n becomes exactly 5*10^5. Then we could do something like this:

```
import compgen

A = 10**9
SN = 5*10**5
def many_cases(rand, new_case, *args):
    ''' generates multiple cases that will be distributed to multiple files '''
    T, N = map(int, args[:2])
    for n in [1, N/10, N/2, 9*N/10, N]:
        for x in xrange(8):
            # generate a case where all numbers are == x mod 8
            @new_case(n, x, n=n)
            def make_case(rand, n, x):
                return [rand.randrange(-A + (x + A) % 8, A + 1, 8) for i in xrange(n)]


@compgen.listify
def distribute(rand, new_case, casemakers, *args):
    T, N = map(int, args[:2])
    def fill_up(group, totaln):
        ''' fill up the file with a bunch of cases so the total n is as close as possible to SN '''
        while len(group) < T and totaln < SN:
            n = min(N, SN - totaln)
            group.append
            @new_case(n)
            def make(rand, n):
                return [rand.randint(-A, A) for i in xrange(n)]
            totaln += n
        return group

    group = []
    totaln = 0
    for cas in rand.shuff(casemakers):
        if not (len(group) < T and totaln + cas.n <= SN):
            yield fill_up(group, totaln)
            group = []
            totaln = 0
        group.append(cas)
        totaln += cas.n
    if group: yield fill_up(group, totaln)

if __name__ == '__main__':
    from case_formatter import print_to_file
    from sys import argv, stdout

    compgen.write_nth_group_to_file(int(argv[1]), print_to_file, many_cases, distribute, argv[2:], stdout)
```

Here, the keyword arg `n=n` passed to `new_case` is what allows us to access `n` in distribute, even though the case hasn't been generated yet. In general, keyword arguments allows one to store any useful info in the ungenerated cases in case you need them, without needing to generate the case itself.  



# Detecting subtasks  

You have a bunch of files and you want to be saved the trouble of determining which subtask(s) each file belongs to. We can automate the process.  

First, write a custom script that detects the subtask(s) of a file. For example, we can write the following:

```
maxn = 0
for cas in xrange(input()):
    n = input()
    raw_input()
    maxn = max(n, maxn)
if maxn <= 10: print 1,
if maxn <= 1000: print 2,
print 3
```

It just prints all subtasks as separate tokens. If we wrote this in a file named `detect_subtasks.py`, then we can use the command `python detect_subtasks.py`. It will take input from stdin.

Alternatively, if we're lazy, we can use the validator we wrote above and just run it across all subtasks, and print those where it passes. This is a bit slower, but only by a constant. In fact, the custom script `subtasks_from_validator` automates the process for you. We can simply run the following command (supposing the only subtasks are 1, 2 and 3):

```
./subtasks_from_validator "python2 validator.py" 1 2 3
```

This takes input from stdin, so if needed, use pipe, or add `< file_to_detect_subtasks.in` at the end.

(If it says `Permission denied`, just add executable permission using `chmod`, like `chmod +x subtasks_from_validator`. If it still fails, it probably means bash is not found in `/bin/bash`. I don't know what's the best way to fix this actually. Just replace the first line of the script, haha.)

Either way, once you have a command that detects subtasks, you can just loop across all files using `all_files_subtasks`: 

```
./all_files_subtasks "tests/*.in" [command to detect subtasks]
```

The `"tests/*.in"* argument matches all files you want to extract subtasks for.

For example, using the commands above,

```
./all_files_subtasks "tests/*.in" python detect_subtasks.py
# or
./all_files_subtasks "tests/*.in" ./subtasks_from_validator "python2 validator.py" 1 2 3
```







# Converting to HackerRank format  

Suppose you downloaded a collection of test cases formatted Polygon-style, and you would like to convert it into a format suitable for uploading to HackerRank. I have a ready-made script for you.

```
./convert_to_hackerrank path/to/tests
```

Here, `path/to/tests` is the tests folder of the Polygon-style package. It contains all test data.









# Writing directly to HackerRank format  

Although not recommended, if you don't want to use Polygon, you can also generate everything locally using the following:

1. Write a testset script similar to the one in polygon, but in bash. Note that you need to use the "$$$" symbol for test enumeration, and that the string "$$$" cannot appear anywhere else in the script. e.g.

```
pypy single_case.py 10 10 > $$$
pypy single_case.py 10 100 > $$$
for x in $(seq 0 3)
do
    pypy multifile_case.py $x 10 100 > $$$
done
```

*Warning*: Behind the scenes, this will be converted to a bash file with "$$$" replaced; it is highly recommended not to make syntax errors; I make no guarantees on what could go wrong if it fails.

2. Use the `./direct_to_hackerrank` program to interpret this script. This requires a validator, a working solution.

```
./direct_to_hackerrank testset_script_file "pypy validator.py" "pypy solution.py" 1 2 3
```

This will generate two folders, `input` and `output`. (Their contents will be deleted initially.) The `output` folder will be populated automatically from the provided solution. They will also be validated, and subtasks will be detected. `1 2 3` are the subtasks; if you leave it empty, then 

Note: If you just want to generate the test without a validator and/or a working solution, use `:` to accept all files as valid and/or print dummy answer files, respectively.




# Testing a solution locally with files in HackerRank format

One can use the handy `./hr` script to test solutions and regenerate the output files without generating the input files again.

```
# to generate output files in output/
./hr genout pypy solution.py
# to test against the output files
./hr test pypy solution.py
# same as 'test', but doesn't print the output of diff
./hr testc pypy solution.py
# to just run a program across all input files
./hr run pypy solution.py
```



# Checkers

TODO add support for checkers




# Converting to other formats  

This is TODO. Conversion 

TODO  

- CodeChef  
- Kattis  
- PC2  



# Testing solutions  

