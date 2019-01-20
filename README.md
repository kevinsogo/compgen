Some useful programs that will help you write data generators, checkers and validators for polygon and hackerrank.





# Example Problem

Given an array, print the sum of its elements.

The input format is as follows.

(Single test):

    N
    A1 A2 ... AN

(Multitest):
    
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

Single test:

```
from __future__ import print_function

def print_to_file(file, arr):
    print(len(arr), file=file)
    print(*arr, sep=' ', file=file)
```

Multitest:

```
from __future__ import print_function

def print_to_file(file, cases):
    for arr in cases:
        print(len(arr), file=file)
        print(*arr, sep=' ', file=file)

```






# Validating a file


`compgen` contains `testlib`-like functions for validating a file. One can alternatively just use testlib here, but there are some other reasons to use this library:

- So that the generator files below can possibly import the validator.
- So that we can test for subtasks.  
- So that we don't have to worry about overflow and undefined behavior.  



Multitest, no subtasks:


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
    ensure(lim.totaln.contains(totaln))

if __name__ == '__main__':
    from sys import stdin
    validate_file(stdin)

```

Note that using `Task` is completely optional. `.read_int` can also be called like this: `file.read_int(1, 10**5)`.  

Note: `.read_ints` method coming up in the future!


Multitest, no subtasks:


```
from compgen import Interval, Task, validator, ensure


subtasks = {
    1: {
        'n': Interval(1, 10),
    },
    2: {
        'n': Interval(1, 1000),
    }
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

    ... # same as above

if __name__ == '__main__':
    from sys import stdin
    validate_file(stdin)
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
    retun cases

if __name__ == '__main__':
    from case_formatter import print_case
    from sys import argv, stdout

    compgen.write_to_file(print_case, random_case, argv[1:], stdout)
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
    from case_formatter import print_case
    from sys import argv, stdout

    compgen.write_to_file(print_case, random_case, argv[1:], stdout)
```


If you want to validate before printing, make the `validate_file` function above importable, then you could replace the last line inside `if __name__ == '__main__':` with this this:

```
    from case_validator import validate_file # import the validate_file function
    compgen.write_to_file(print_case, random_case, stdout, validate=lambda f: validate_file(f, subtask=1))
```





# Generating multiple files simultaneously

Sometimes, you just want to create several kinds of cases without worrying about how to distribute them into different files. Of course, you could generate all cases first, arranging them, then calling `write_to_file` multiple times. This works if you're only generating locally. But this has a downside: Polygon wants each generator to make only one file. One could just ignore the rest of the files, but this is still quite slow since you're generating all the cases every time. What we want is a way to only generate the necessary files without worrying about distributing into files.  

You can use this pattern:

```
import compgen

A = 10**9
def make_case(rand, n):
    return [rand.randint(-A, A) for i in xrange(n)]

def many_cases(rand, new_case, T, N, *args):
    for n in [1, N/10, N/2, 9*N/10, N]:
        for x in xrange(10):
            # generate a case where all numbers are == x mod 10
            @new_case(n, x)
            def make_case(rand, n, x):
                return [rand.randint(base + (x - base) % 10, A, 10) for i in xrange(n)]

    while new_case.total_cases % T:
        new_case(N)(make_case)


def distribute(rand, new_case, casemakers, T, N, *args):
    return compgen.group_into(T, rand.shuff(casemakers)) # shuffle and then divide into groups of size T

if __name__ == '__main__':
    from case_formatter import print_case
    from sys import argv, stdout

    compgen.write_nth_group_to_file(int(argv[1]), print_case, many_cases, distribute, argv[2:], stdout)
```


The function decorated by `new_case` must contain the bulk of work needed to generate that case; that way, the work is not done for cases that will not be needed. One also needs to pass `n` and `x` through it to capture their values.

(should I just use a lazily-evaluated language for this? haha)

`distribute` is responsible for distributing the (ungenerated) cases into files. One can choose to generate additional cases here. For example, suppose we want to fill in each file with extra cases so that total n becomes exactly 5*10^5. Then we could do something like this:

```

import compgen

A = 10**9
SN = 5*10**5
def make_case(rand, n):
    return [rand.randint(-A, A) for i in xrange(n)]

def many_cases(rand, new_case, T, N, *args):
    for n in [1, N/10, N/2, 9*N/10, N]:
        for x in xrange(10):
            # generate a case where all numbers are == x mod 10
            @new_case(n, x, n=n)
            def make_case(rand, n, x):
                return [rand.randint(base + (x - base) % 10, A, 10) for i in xrange(n)]


@compgen.listify
def distribute(rand, new_case, casemakers, T, N, *args):
    for group in compgen.group_into(T, rand.shuff(casemakers)):
        totaln = sum(cas.n for cas in group)
        while len(group) < T and totaln < SN:
            n = min(N, SN - totaln)
            @group.append
            @new_case(n)
            def make(rand, n):
                return make_case(rand, n)
            totaln += n
        yield group


if __name__ == '__main__':
    from case_formatter import print_case
    from sys import argv, stdout

    compgen.write_nth_group_to_file(int(argv[1]), print_case, many_cases, distribute, argv[2:], stdout)
```




# Detecting subtasks  

You have a bunch of files and you want to be saved the trouble of determining which subtask(s) each file belongs to.  

TODO






# Converting to HackerRank format  

Suppose you downloaded









# Writing directly to HackerRank format  

Although not recommended, if you don't want to use Polygon, one can generate everything locally using the following:

1. Write a testset script similar to the one in polygon, but in bash. Note that you need to use the "$$$" symbol for test enumeration, and that the string "$$$" cannot appear anywhere else in the script. e.g.

pypy single_case.py 10 100 > $$$
pypy single_case.py 10 1000 > $$$
for x in $(seq 0 9)
do
    pypy multifile_case.py $x 10 100 > $$$
done

2. Use the `TODO` program to compile this script into a bash file. This requires a validator.


<!-- 
assert '$$$$' not in script
$$$ replaced by >(tee filename | validator)
generate solutions
detect subtasks

this formats it CF-style.
 -->


3. Run the generated bash file. This will generate two folders, `input` and `output`. The `output` folder will be populated automatically from the provided solution. They will also be validated, and subtasks will be detected. 







# Converting to other formats  

This is TODO. Conversion 

TODO  

- CodeChef  
- Kattis  
- PC2  



# Testing solutions  

