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
def validate_file(file): # file-like object ('validator' wraps it additional properties)
    lim = Task(bounds)

    t = file.read_int(lim.t)
    totaln = 0
    for cas in xrange(t):
        n = file.read_int(lim.n)
        totaln += n
        file.read_eoln()
        # file.read_ints coming up in the future
        a = []
        for i in xrange(n):
            a.append(file.read_int(lim.a))
            (file.read_space if i < n - 1 else file.read_eoln)()

    file.read_eof()
    ensure(lim.totaln.contains(totaln))
```




Multitest, no subtasks:


```
from compgen import Task, validator, interval_contains, ensure


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
```

