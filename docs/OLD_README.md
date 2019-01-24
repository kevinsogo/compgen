<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE; EDIT readme_src/docs/OLD_README_TEMPLATE.md INSTEAD, THEN RUN 'python2 gen_readme.py'. -->


Some useful programs that will help you write data generators, checkers and validators for Polygon and HackerRank (and later on, other judges as well), *in Python*.  

Let's go through the whole process. I promise this will be easy!






**Polygon note:** Due to the way Polygon works, we have to do some hacks so that we are able to use this there. **If you want to use this for Polygon, you need to follow these rules:**

- Any `import`, aside from builtin packages, must be of the following form: `from xxx import *`. (It should be an asterisk `*`.) It will not work otherwise. In addition, these import statements must be unindented.

- Don't print anything to stderr for validators and generators; Polygon will interpret it as an error. (Of course, unless you really want to signal an error.) But if you're printing something anyway, you need to add the line `from __future__ import print_function` at the beginning of your code. Ideally, you don't import anything else from `__future__`, though in some cases it would work. 

- You cannot upload any code you write directly into Polygon; you have to run the following command first: `polygonate`. This will generate a folder called `polygon_ready`; the files inside it can now be uploaded. 

*Note:* It would be great if the path containing `compgen` AND the location of the problem data you're working on doesn't have spaces and other special characters in it; I haven't tested if the scripts work if there are. 

*Note:* Some of the scripts below make use of some temp files, so running multiple instances simultaneously could cause some problems. Please don't run multiple scripts simultaneously.



# Example Problem

Let's use this problem as an example. 

**Statement**  

Given an array, print the sum of its elements.

**Input Format**  

    T
    N
    A1 A2 ... AN
    N
    A1 A2 ... AN
    ...
    N
    A1 A2 ... AN




**Constraints**  

$1 \le T \le 10^5$  
$1 \le N \le 10^5$  
$\sum N \le 5\cdot 10^5$  
$-10**9 \le A_i \le 10^9$  

**Subtask 1**: $N \le 10$  
**Subtask 2**: $N \le 1000$  
**Subtask 3**: No additional constraints  




# Printing a case to a file

This just takes a test case and prints it to a file in the correct input format. I suggest writing it on a separate file on its own, say `formatter.py`, so that it could be imported later.  

```python
from __future__ import print_function

def print_to_file(file, cases):
    print(len(cases), file=file)
    for arr in cases:
        print(len(arr), file=file)
        print(*arr, sep=' ', file=file)
```







# Validating a file


`compgen` contains testlib-like functions for validating a file. You can alternatively just use testlib here, but there are some other reasons to use this library instead:

- So that the generator files below can possibly import the validator.
- So that we can detect subtasks (explained later).  
- So that we don't have to worry about overflow and undefined behavior.  
- So that you use Python and not C++.  
- So that you use Python and not C++.  
- So that you use Python and not C++.  

A validator should take input from stdin. It should return with 0 exit code iff the input is valid.

Here's an example of a validator:

```python
from __future__ import print_function
from compgen import *

bounds = {
    't': Interval(1, 10**5),
    'n': Interval(1, 10**5),
    'totaln': Interval(0, 5*10**5),
    'a': Interval(-10**9, 10**9),
}

@validator
def validate_file(file):
    lim = Bounds(bounds)

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

*Note:* Using things like `Interval` and `Bounds` is completely optional; `.read_int` can also be called like `.read_int(1, 10**5)`. However, using `ensure` is recommended. (It is similar to `assert`.)

*Note:* There is also a `.read_ints` method!

**Polygon note:** This file can be used as the "validator" in Polygon (after running the `polygonate` script). Also, notice that `compgen` is imported with the form `from ... import *`.

Here's a validator that can also check subtasks:

```python
from __future__ import print_function
from compgen import *

subtasks = {
    '1': {
        'n': Interval(1, 10),
    },
    '2': {
        'n': Interval(1, 1000),
    },
    '3': {
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
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

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
    subtask = argv[1] if len(argv) > 1 else None
    validate_file(stdin, subtask=subtask)
```

This takes the subtask name as an argument. The `&` operator merges intervals of two `Bounds` objects.

*Note:* Use integer literals as subtask names. This will be required later on.

**Polygon note:** It is important that such a subtask checker must not reject if the subtask name (`argv[1]`) is invalid. This is because Polygon calls the validator with some command line arguments, and so the first of those arguments (usually something like `--testset`) gets interpreted as a subtask name.






# A test data generator

It's easy to write a test generator.  

```python
from __future__ import print_function
from compgen import *
from formatter import *

A = 10**9

def random_cases(rand, *args):
    T, N = map(int, args[:2])
    cases = []
    for cas in xrange(T):
        n = rand.randint(1, N)
        cases.append([rand.randint(-A, A) for i in xrange(n)])
    return cases

if __name__ == '__main__':
    from sys import argv, stdout

    write_to_file(print_to_file, random_cases, argv[1:], stdout)
```

**Polygon note:** Note that `formatter` is imported using the form `from ... import *`.

The random seed will be based on `argv[1:]`.  

*Note:* Don't import `random`! Instead, use the provided random number generator `rand`. This ensures reproducibility.  

**Polygon note:** You can write files like this and use them under "tests". The usage is very similar to generators written with testlib.

You can make it slightly cleaner by using the convenience function `listify`.  

```python
from __future__ import print_function
from compgen import *
from formatter import *

A = 10**9

@listify
def random_cases(rand, *args):
    ''' generates test data for a file '''
    T, N = map(int, args[:2])
    for cas in xrange(T):
        n = rand.randint(1, N)
        yield [rand.randint(-A, A) for i in xrange(n)]

if __name__ == '__main__':
    from sys import argv, stdout

    write_to_file(print_to_file, random_cases, argv[1:], stdout)
```

If you want to validate before printing, make the `validate_file` function above importable, then you could replace the last line with this:

```python
from validator import *
...
    compgen.write_to_file(print_to_file, random_cases, argv[1:], stdout,
            validate=lambda f: validate_file(f, subtask=1))
```

**Polygon note:** Again, `from ... import *`.





# Generating multiple files simultaneously

Sometimes, you just want to create several kinds of cases without worrying about how to distribute them into different files. Of course, you could generate all cases first, arrange them, then call `write_to_file` multiple times. But this library provides an easier way of generating a bunch of cases without worrying too much about distributing to different files.

You can use this pattern:

```python
from __future__ import print_function
from compgen import *
from formatter import *

A = 10**9
def rand_case(rand, n):
    ''' just random data '''
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
        new_case(N)(rand_case)


def distribute(rand, new_case, casemakers, *args):
    T, N = map(int, args[:2])
    return group_into(T, rand.shuff(casemakers)) # shuffle and then divide into groups of size T

if __name__ == '__main__':
    from sys import argv, stdout

    index = int(argv[1])
    write_nth_group_to_file(index, print_to_file, many_cases, distribute, argv[2:], stdout)
```

This "lazily" generates all test data and groups them into some number of files, but only prints out the `index`th group.

The function decorated by `new_case` must contain the bulk of work needed to generate that case; that way, the work is not done for cases that will not be needed. Notice that we also need to pass `n` and `x` through it, since we need to capture their values. (should I just use a lazily-evaluated language for this? haha)

`distribute` is responsible for distributing the (ungenerated) cases into files. The `group_into` convenience function makes it easy to split the files into groups of equal size.  

You may optionally choose to generate additional cases in `distribute`. For example, suppose we want to fill in each file with extra cases so that the sum of $N$s becomes exactly $5\cdot 10^5$ (or as close to it as possible). Then we could do something like this:

```python
from __future__ import print_function
from compgen import *
from formatter import *

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


@listify
def distribute(rand, new_case, casemakers, *args):
    T, N = map(int, args[:2])
    def fill_up(group, totaln):
        ''' fill up the file with a bunch of cases so the total n is as close as possible to SN '''
        while len(group) < T and totaln < SN:
            n = min(N, SN - totaln)
            @group.append
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
    from sys import argv, stdout

    index = int(argv[1])
    write_nth_group_to_file(index, print_to_file, many_cases, distribute, argv[2:], stdout)
```

Here, the keyword arg `n=n` passed to `new_case` is what allows us to access `n` in `distribute`, even though the case hasn't been generated yet. In general, the keyword arguments allow you to store any useful info about the ungenerated case if you need them, without needing to generate the case itself.  



# Detecting subtasks  

You have a bunch of files and you want to be saved the trouble of determining which subtask(s) each file belongs to. We can automate the process.  

First, write a custom script that detects the subtask(s) of a file. For example, we can write the following:

```python
maxn = 0
for cas in xrange(input()):
    n = input()
    raw_input()
    maxn = max(n, maxn)
if maxn <= 10: print 1,
if maxn <= 1000: print 2,
print 3
```

It just prints *all* subtasks as separate tokens. If we save this in `detect_subtasks.py`, then we can use it with `python2 detect_subtasks.py`. It will take input from stdin.

Alternatively, if we're lazy, we can use the validator we wrote above and just run it across all subtasks, and print those where it passes. This is a bit slower, but only by a constant (proportional to the number of subtasks). In fact, the script `subtasks_from_validator` automates this for you! We can simply run the following command (supposing the only subtasks are 1, 2 and 3):

```bash
subtasks_from_validator 1,2,3 python2 validator.py
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
all_files_subtasks "tests/*.in" subtasks_from_validator 1,2,3 python2 validator.py
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
python2 single_case.py 10 10 > $$$
python2 single_case.py 10 100 > $$$
python2 single_case.py 10 1000 > $$$
python2 single_case.py 10 10000 > $$$
for x in $(seq 0 3)
do
    python2 multifile_cases.py $x 10 20 > $$$
done
```


2. Use the `direct_to_hackerrank` program to interpret this script. This requires a validator and a working solution.

```bash
direct_to_hackerrank testset_script_file "python2 validator.py" "python2 solution.py" 1,2,3
```

This will generate two folders, `input` and `output`. (Their contents will be deleted initially.) The `output` folder will be populated automatically from the provided solution. They will also be validated, and subtasks will be detected. In the example above, `1,2,3` are the subtasks. If you don't provide these arguments, then it will assume that the task doesn't have subtasks.

**Warning**: Behind the scenes, the testset script will be converted to a bash file with `$$$` replaced by something, and some lines inserted before and after, hence, it is highly recommended to keep your script simple. I make no guarantees on what could go wrong if it fails!

*Note:* If you just want to generate the inputs without a validator and/or a working solution, use `echo` as a substitute. As a "validator", it accepts all files as valid. As a "solution", it just prints dummy answer files. e.g.

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

Some problems require a custom judge/checker to evaluate submissions. The `compgen.checkers` module provides a simple way to write checkers that can support several platforms. (just HackerRank and Polygon for nwo)

## Sample Problem  

Here's an example of such a problem:

**Statement**  

Given an array, find the longest subsequence consisting of distinct elements. If there are multiple, any one will be accepted.

**Input Format**  

    T
    N
    A1 A2 ... AN
    N
    A1 A2 ... AN
    ...
    N
    A1 A2 ... AN

**Output Format**  

    M
    B1 B2 ... BM
    M
    B1 B2 ... BM
    ...
    M
    B1 B2 ... BM


**Constraints**  

$1 \le T \le 10^5$  
$1 \le N \le 10^5$  
$\sum N \le 5\cdot 10^5$  
$-10**9 \le A_i \le 10^9$  

**Subtask 1**: $N \le 10$  
**Subtask 2**: $N \le 1000$  
**Subtask 3**: No additional constraints  

The standard procedure of making test data and validators is basically the same, but now we also have to write a custom checker since there are several acceptable solutions.  

## Writing checkers

The most general template for custom checkers is the following:

```python
from __future__ import print_function, division, unicode_literals, absolute_import
from compgen.checkers import *

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    # write your grader here
    
    # Raise this if the answer is incorrect
    raise WA("The contestant's output is incorrect!")
    
    # Raise this if the judge data is incorrect, or if the checking fails for some reason other than WA
    # Any other exception type raised will be considered equivalent to Fail.
    raise Fail("The judge data is incorrect. Fix it!")

    # the return value is the score, and must be a value between 0.0 and 1.0
    return 1.0 

if __name__ == '__main__': chk()
```

Here, `input_file`, `output_file` and `judge_file` are of the same data type and are self-explanatory. They are iterators that enumerate the distinct *lines* of each file.

However, there are a couple of constraints:

- As above, the import line has to be exactly `from compgen.checkers import *`.
- You *must* write the exact same future import statement in the first line, for all checkers.

Both are due to technical reasons arising from the constraints of the judging platforms we're using. Please just follow them.

Here's an example for our problem above:

```python
from __future__ import print_function, division, unicode_literals, absolute_import
from compgen.checkers import *

def get_sequence(file, exc=Exception):
    try:
        m = int(file.next().rstrip())
        b = map(int, file.next().rstrip().split(' ')) # stricter
    except Exception as e:
        raise ParseError("Failed to get a sequence: " + str(e))
    ensure(m >= 0, "Invalid length", exc=exc)
    ensure(len(b) == m, lambda: "Expected {} numbers but got {}".format(m, len(b)), exc=exc)
    return b

def check_valid(a, b, exc=Exception):
    # check subsequence
    j = 0
    for i in xrange(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=exc)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@set_checker()
def check_solution(input_file, output_file, judge_file, **kwargs):
    z = int(input_file.next())
    for cas in xrange(z):
        n = int(input_file.next())
        a = map(int, input_file.next().strip().split())
        if len(a) != n:
            raise Fail("Judge input invalid")
        cont_b = get_sequence(output_file, exc=WA)
        judge_b = get_sequence(judge_file, exc=Fail)
        check_valid(a, cont_b, exc=WA)
        check_valid(a, judge_b, exc=Fail)
        if len(cont_b) < len(judge_b): raise WA("Suboptimal solution")
        if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")

    if output_file.has_next(): raise WA("Extra characters at the end of the output file")
    if judge_file.has_next(): raise Fail("Extra characters at the end of the judge file!")
    return 1.0

if __name__ == '__main__': chk()
```

Note that, even though the judge data should be absolutely correct, the custom checker shouldn't assume so, and must raise `Fail` if it detects that something is wrong. This is better than silently ignoring the problem and risking incorrect judgement.

The `set_checker()` decorator can take some arguments. Here are some possible uses:

```python
@set_checker('tokens') # Split by tokens instead of split by lines.

@set_checker('tokens', 'lines', 'tokens') # If you want different files to have different tokenizing styles.

@set_checker(no_extra_chars=True) # Automatically detect that all files have been read completely,
                                  # and issue a WA/Fail otherwise. This is to give the correct verdict in
                                  # cases where the contestant outputs extra characters/lines at the end.
```

## Convenient single-case and multi-case checker

A lot of the times, we don't need the full power of checkers above. Most checkers you'll write will be of the following form:

1. Read the input from `input_file`.  
2. Read the contestant's output from `output_file`.
3. Read the judge's data from `judge_file`.
4. Analyze all three things and determine the score, usually just 0.0 or 1.0.  

or, if the problem has several test cases,

- Read the number of test cases from `input_file`, say `t`.  
- Do the above `t` times.  
- Take the minimum of the scores as the final score.

These are not that hard to write (as shown above), but since they're so common, I've provided convenience functions `set_single_checker()` and `set_multi_checker()` to make it much easier. Here's an example:

```python
from __future__ import print_function, division, unicode_literals, absolute_import
from compgen.checkers import *

@chk.get_one_input
def get_one_input(file, **kwargs):
    n = int(file.next())
    a = map(int, file.next().strip().split())
    ensure(len(a) == n, "Invalid length in input", exc=Fail)
    return a

@chk.get_output_from_input
@chk.get_judge_data_from_input
def get_output_from_input(file, a, **kwargs):
    exc = kwargs['exc']
    try:
        m = int(file.next().rstrip())
        b = map(int, file.next().rstrip().split(' ')) # stricter
    except Exception as e:
        raise exc("Failed to get a sequence: " + str(e))
    ensure(m >= 0, "Invalid length", exc=exc)
    ensure(len(b) == m, lambda: "Expected {} numbers but got {}".format(m, len(b)), exc=exc)
    return b

def check_valid(a, b, exc=Exception):
    # check subsequence
    j = 0
    for i in xrange(len(a)):
        if j < len(b) and a[i] == b[j]: j += 1
    ensure(j == len(b), "Not a subsequence!", exc=exc)
    # check distinct
    ensure(len(b) == len(set(b)), "Values not unique!", exc=exc)

@set_multi_checker(no_extra_chars=True)
def check_solution(a, cont_b, judge_b, **kwargs):
    check_valid(a, cont_b, exc=WA)
    check_valid(a, judge_b, exc=Fail) # remove for speed
    if len(cont_b) < len(judge_b): raise WA("Suboptimal solution")
    if len(cont_b) > len(judge_b): raise Fail("Judge data incorrect!")
    return 1.0

if __name__ == '__main__': chk(title="Split")
```

You simply have to write four functions and decorate them accordingly. They should be self-explanatory.

If there was only one test case, you simply replace `set_multi_checker` with `set_single_checker`!

## Uploading to judges

As before, you can't immediately upload these files as checkers. Here's what to do:

For **Polygon**: Just run `polygonate`; checkers will be included.

For **HackerRank**: Run `hrate`; similar to `polygonate`, this will create a folder called `hr_ready` which will contain the snippet of checker codes that can be uploaded to HackerRank.

If you wish to grade subtasks as well, you need to create a file called `details.json` and describe the subtasks there. It will look something like.

```json
{
    "title": "Split",
    "valid_subtasks": [1, 2, 3],
    "subtasks_files": [
        [[0, 0], [1, 2, 3]],
        [[1, 2], [2, 3]],
        [[3, 3], [3]]
    ],
    "comments": [
        "Anything can go here. This will not be read by the scripts. It can also be removed completely.",
        "Each entry in 'subtasks_files' is of the form '[[low_index, high_index], [ list of subtasks ]]'",
        "[low_index, high_index] represents a range of files under those subtasks.",
        "Each file must appear in exactly one range.",
        "IMPORTANT: The last file of each subtask must be unique to that subtask. (HackerRank restriction)"
    ]
}
```

You can also automate this process by running the `make_details` script, which takes the same arguments as `all_files_subtasks`. This is also automatically created by `direct_to_hackerrank`.  

For other platforms: Will support in the future.


# Converting to other formats  

This is TODO. Conversion...

TODO  

- CodeChef  
- Kattis  
- PC2  



# Random notes, observations  

- In general, the *pathname* of `compgen` and the problem directory you're working on must not have spaces or other special characters; the scripts I wrote are a bit haphazard and may not work otherwise. 

- Polygon annoyingly has an old python version, which means that some programs that run for you might not run there. Be careful! For example:
    
    - Don't use xrange with arguments exceeding C long.

- Feel free to request features/changes/improvements you'd like to see.

- Feel free to make a merge request!






# Help needed  


**Important**  

- Do something about the fact that Python's `random` module makes no guarantees of reproducibility across implementations and platforms; see [this](https://stackoverflow.com/questions/8786084/reproducibility-of-python-pseudo-random-numbers-across-systems-and-versions).
- Give a better name than "compgen". We can still rename this package while it's early.    
- Ensure that multiple instances of the scripts can be run simultaneously, at least the common ones.

**Others**  

- Implement missing features above. 
- Improve scripts. Possibly look for mistakes. And badly-written parts. In particular, some bash scripts are quite janky, unidiomatic or just plain buggy.
- Improve `StrictStream`. Right now, I'm manually buffering 10^5 characters at a time, but I think there has to be a more idiomatic way to buffer.  
- Write unit tests, possibly.  
- Come up with better naming practices/conventions.
- Ensure that the scripts work even in path names containing spaces and special characters. 
- Improve `polygonate` to reduce the restrictions above. For example, better handling of other forms of `import`.
- Copy `random.py` to guarantee reproducibility. 
- More error handling in scripts; in general, make them more robust.
- Improve the readme by separating it into parts. (`gen_readme.py` should still generate them all.) The current readme is more like a tutorial. haha
    
    - We could have separate pages for validators+generators, local scripts, and custom checkers.
    - README.md would just contain a small overview.
    - Maybe the Polygon notes can be compiled into their own section as well.

- Move the convenience functions common to `compgen` and `compgen.checkers` to a separate file, so they can be imported by both. Extend `polygonate` and `hrate` to handle it.

**To consider**  

- Make the `direct_to_hackerrank` command look like:

    ```
    direct_to_hackerrank testset_script_file -- validator command -- solution command -- subtasks
    ```

    The idea is that `--` can be replaced by any token not appearing in the validator and solution commands. 

- Convert all scripts to Python in case no one knows (or likes to work with) Bash.

- Use gitlab's "Issues" feature and write these things there instead.  

- Generalize `hr` to any of the supported formats. e.g. `localdata`. `hr` will then be an alias of `localdata hackerrank`, but we will have `poly` = `localdata polygon`, `cc` = `localdata codechef`, `localdata kattis`, `localdata pc2`.  

- Make conversion between different formats seamless. `convert_data polygon hackerrank`, `convert_data hackerrank polygon`. The base format could be in one single folder with `.in` and `.ans` extensions. When uploading to hackerrank, a new script will convert them to hackerrank's zip format (without leaving traces of the `input/` and `output/` folder).

    - Preferably, testing (via `hr`-like scripts) is still possible on all supported formats.
