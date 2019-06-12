This is a tutorial on how to prepare problems from scratch using KompGen. We'll work through preparing the [NOI.PH 2019 Finals Practice Round](https://hackerrank.com/contests/noi-ph-2019-finals-practice) together, and while doing so, we'll go over many of the features of KompGen that you'll use during problemsetting.

I'll assume you have `kg` installed in your system. You can check this by typing `kg` in the termiinal, which should pop up a message like this:
```bash
$ kg
usage: kg [-h] [--krazy]
          {konvert,convert,konvert-sequence,convert-sequence,subtasks,gen,test,
          run,make,joke,init,kompile,compile,kontest,contest,seating,passwords}
          ...
kg: error: the following arguments are required: main_command
```

If you don't get a message like this, check out the Setup header in the README.

I'll also assume some proficiency with [Python](https://docs.python.org/3/tutorial/), as we'll work exclusively in Python throughout this tutorial. (It's possible to use different languages, but if you're using KompGen in the first place, you're probably interested in doing everything in Python anyway.) I'll try not to use anything too magical in Python, and stick to basic language functions.

To avoid any issues later on, if you're using Windows, I'll strongly recommend you [install Gow](https://github.com/bmatzelle/gow/wiki) if you haven't yet. It will give you some useful programs like `cat` or `diff` (and if you don't know what these are, don't worry about it).


# Overview

The process of making a programming problem is called *problemsetting*, or simply *setting*. Setting a problem involves writing several different files: the statement, the validator, generators, the checker, the model solution, and so on. In this section, I'll introduce what each of these are and what they do.

## The model solution and the checker

I'll assume you're familiar with the way that solutions to competitive programming problems are judged. As a reminder, the way a solution to a (typical, non-interactive) problem is judged works like this:

1. The contestant's *solution* is run over several *test cases*.

2. The contestant's output for each case is compared to the output of the *model solution* by a program called the *checker*.

3. The checker determines whether the contestant's output is correct.

This introduces us to our first two programs. The first is the **model solution**. As the name suggests, it's the solution that a contestant's solution is compared against. The programs aren't directly compared, but their outputs are. Sometimes, this is also called the *judge solution*.

The second is the **checker**. For most problems, the checker will simply determine if the outputs of the contestant and the model solution are the same. You may also be familiar that when the answer is a float, an answer is accepted if its absolute or relative error is within certain bounds---this is also handled by the checker. For problems with multiple possible solutions, it's also the checker that determines whether a contestant's output is correct.

## Strong test cases and generators

This leads us to the next question: how are test cases written? You're probably familiar, or at least have heard of, the difference between *weak* test cases and *strong* test cases. The aim of test cases are to rule out wrong and slow solutions. Test cases that are *strong* do this well:

- They include *large* test cases that a slow solution would exceed the time limit on, but which a correct solution would pass. Ideally, these should be written in a way that solutions with the correct time complexity but a large constant should still pass, but heavily-optimized solutions with a slower time complexity should fail.

- They include *tricky* test cases that a wrong solution would produce the wrong answer for, but which a correct solution would pass. These test cases should catch common mistakes, like off-by-one errors, stack overflows, incorrect binary searches, or tricky edge cases.

We see that strong test cases fall into two types: *large* and *tricky*. Strong test cases include both large and tricky test cases. It's also usually a good idea to also include some smaller test cases, in order to quickly rule out incorrect solutions.

Good test cases also have a limited number of them. While it's possible to simply put all possible inputs as test cases, this often requires making a huge amount of test cases. Problems typically have less than one hundred or so test cases, and the total size of all input should be a few dozen megabytes at most.

On the other hand, weak test cases are those that aren't strong. For example, if all the test cases for a problem are made by hand, then this is very likely to produce weak test cases. Purely random test cases are often weak as well, since they won't include large or tricky test cases.

As you can probably guess, **the hardest and most important part in problemsetting is writing strong test cases**. This is tricky because they need to be strong, and yet they need to be limited. The easiest way to accomplish this is not to write these test cases by hand, but by using programs called *generators*.

This introduces us to our next program: **generators**. Generators are programs that make test data. Note how I used the plural *generators*. Usually, there would be one generator for each kind of test case: random test cases, tricky test cases, edge cases, test cases with specific patterns, and so on.

## The validator

If you've joined a Codeforces round and have participated in the hacking phase, then you should know the process for hacking:

1. You read a contestant's solution and come up with a test case.

2. The test case is checked if it matches the input format for the problem by a program called the *validator*.

3. The contestant's solution is run on this test case, and its output is compared to the model solution by the checker.

This introduces us to our last program: the **validator**. The validator is a program that reads in a file and check if it follows the input format given in the problem statement. It should also be very strict in doing so: it should check that there is no extra whitespace, or even extra blank lines.

You may think that a validator is only necessary when writing problems for Codeforces, but *it's important to write a validator for **every** problem*. This is because in the KompGen model, all test cases made by a generator are run through the validator in order to check if they're valid. This ensures that invalid test data does not appear during the contest.

In the KompGen model, the validator is also used to detect subtasks, which is useful so you don't have to assign subtasks yourself.

## The statement

Finally, you should also remember to write the **statement**. This consists of the problem statement, the input and output format, the constraints and scoring, and some sample test cases.

By now, you should be familiar with what separates good statements from bad ones. Good statements are clear and unambiguous, carefully defining everything stated. Here are some examples of sentences that shouldn't appear in a good statement, lifted from the NOI.PH's document *Preparing Programming Contests Essentials*:

- *The piece can move one step in the two-dimensional grid.* Which directions are allowed for one step? Can the piece move one step diagonally? What happens at the edges of the grid: can the piece move out of the grid?

- *Jennifer must sit to the right of Geniefer.* Must Jennifer sit immediately next to Geniefer? Can she sit a few seats away, as long as the seat is to Geniefer’s right?

- *Output the longest string satisfying the constraints above.* The word *the* implies that there's only one such longest string. What if there are multiple longest strings? Or are we guaranteed that there's only one such longest string?

- *The input contains the three integers mentioned in the problem statement.* Which three integers? How are they ordered in the input? Are they given in a single line, or each in a separate line? Are they separated by spaces, commas, or what?

It can be a bit tricky, starting out, getting the problem statement right, especially the input and output formats. We'll talk about ways to write a good statement later on.

## Putting it all together

Phew, that's a lot of stuff! Let's review:

- The **statement** specifies the problem.

- The **generators** make the test cases for the problem.

- The **validator** checks if these test cases follow the input format.

- The **model solution** gives the correct answers to each test case.

- The **checker** checks if a contestant's output is correct.

We introduced these five files in the order checker, model solution, generator, validator, and statement. For this tutorial, we will write these files *in the reverse order*, although it's possible to write these in any order. This means that the process of making a problem is:

1. Write a clear **statement**.

2. Write a **validator** according to the input format and constraints in the statement.

3. Write **generators** that make the test data for the program. This step is typically the hardest part of problemsetting.

4. Write a **model solution**, and be very careful to make sure it's correct.

5. Use one of the default **checkers**, or write your own.

Now that you know how a problem is written, let's set our first problem using KompGen!


# Mystery Function

First, let's set the problem [Mystery Function](https://www.hackerrank.com/contests/noi-ph-2019-finals-practice/challenges/mystery-function). Although it's not the easiest problem in the round, it's the easiest problem to set, because the test data is very simple. I recommend you follow along with the commands on your computer, so that you can see how KompGen works.

## Writing the statement

NOI.PH problems have a template for statements that's different from the one that KompGen (currently) makes, so we'll use this template instead. Here's a very bare statement that illustrates this:

```tex
Title: Mystery Function  
Slug: mystery-function  
Description: ?  
Author: Kevin  


\section{Statement}

You are given an integer $n$. If $n \ge 1$, output $n^3 + n^2 + n + 1$. 
Otherwise, output \texttt{NONE}.


\section{Input Format}

The first line of input contains $t$, the number of test cases.

Each test case consists of one line containing a single integer, $n$.


\section{Output Format}

For each test case, output one line containing the answer to that test case.


\section{Scoring}

\textbf{For all subtasks}

$1 \le t \le 10^5$

\textbf{Subtask 1} (20 points):

$n \in \{1, 2, 3, 69, 420\}$  

\textbf{Subtask 2} (20 points):

$|n| < 10^3$

\textbf{Subtask 3} (60 points):

$|n| < 10^5$



\section{Sample Input}

    1
    1


\section{Sample Output}

    4


\section{Notes}

We have $n = 1$. Hence we output $1^3 + 1^2 + 1 + 1 = 4$.
```

We save this in a file called `statement.tex`. The `.tex` is for [LaTeX](https://www.nyu.edu/projects/beber/files/Chang_LaTeX_sheet.pdf). When problems in the NOI.PH Scientific Committee are at the idea stage, we usually pass around statement files like these.

Observe how carefully the input and output formats are specified. For this problem, it's pretty easy to write the input format: this is the typical template used for input with test cases. Generally, when writing input formats, I just modify the input format from an existing NOI.PH problem. The same goes for output formats.

The only thing here that might not be obvious are the *slug* and *description*. In a HackerRank URL to a problem, the thing that comes after the last slash is called the *slug*. It consists of only lowercase English letters, numbers, and hyphens. We typically also leave the description blank.

<!-- TODO i kinda want to write a better cheatsheet than the linked one. https://math.meta.stackexchange.com/questions/5020/mathjax-basic-tutorial-and-quick-reference might be a good reference. -->

<!-- TODO To help with writing input and output formats, some templates can be found in `STATEMENTS.md`. -->

## Initializing, and details.json

Open your terminal somewhere you're fine putting files in and run the command
```bash
$ kg init mystery-function --subtasks=3
```

Here, `mystery-function` is the slug and `3` is the number of subtasks. Don't worry about getting the number of subtasks right: we can always change it later.

The command makes a folder called `mystery-function` inside the current folder. There will be a bunch of automatically generated files: don't worry too much about these. For now, get rid of the generated `statement.md` and replace it with the `statement.tex` we wrote previously.

Open the file `details.json`. This file is what KompGen uses to determine which files in the folder are which. Whenever you add a new file, you typically want to add it to `details.json` as well. Most of the fields here should be self-explanatory: you have the title, the model solution, the validator, the generators, and the list of subtasks. Don't worry about any of the other fields for now.

The default `details.json` here is fine. Usually I'd change the `title` field, but in this case KompGen is smart enough to figure out the title is "Mystery Function". Let's leave it alone for now, and write the validator!

## Writing the validator

Open the file `validator.py`. You should see a file that looks like:

```python
from sys import *
from kg.validators import * ### @import

subtasks = {
    '1': {},
    '2': {},
    '3': {},
}

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': 1 <= +Var <= 10**5,
}

@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    ... # write your validator here

    # file .read_int(), .read_ints(), .read_space(), .read_eoln(), etc.
    # file.read_eof()
    

if __name__ == '__main__':
    subtask = argv[1] if len(argv) > 1 else None
    if subtask == '--detect-subtasks':
        print(*detect_subtasks(validate_file, stdin, subtasks))
    else:
        validate_file(stdin, subtask=subtask)
```

We won't touch the header, which inputs the required stuff from KompGen. We also won't touch anything after `if __name__ == '__main__':`, so don't worry about it.

First, let's specify the constraints on `t` and `n`, by changing `subtasks` and `bounds`:

```python
subtasks = {
    '1': {},
    '2': { 'n': -10**3 < +Var < 10**3 },
    '3': { 'n': -10**5 < +Var < 10**5 },
}

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': -10**5 < +Var < 10**5,
}
```

<!-- TODO I now actually want to swap bounds and subtasks in the generated template. -->

Here, `bounds` should have the constraints for the variables across all subtasks, and `subtasks` should have any additional constraints. Currently, KompGen doesn't support `or` here. We can't write something like

```python
# doesn't work:
'n': +Var == 1 or +Var == 2  or +Var == 3 or +Var == 69 or +Var == 420
```

So we'll just have to check the bounds for subtask 1 later.

Second, let's write the function `validate_file`, which reads the input format very strictly. To write it, we simply convert each line of the input format. For example, if a line has "three space-separated integers x, y, z", then we write

```python
[x, y, z] = file.read.int(lim.x).space.int(lim.y).space.int(lim.z).eoln
```

The read integers are then placed in `x`, `y`, and `z` if we need to use them later on in the function. Note how everything here is specified, including the whitespace.

More specifically, `int(lim.x)` reads an integer and checks if it follows the limits for `x`, specified in both `bounds` and `subtask`. Then `space` reads a space, `int(lim.y)` reads another integer, and so on. The `eoln` reads the end of line.

For this problem, our `validate_file` function will look like

```python
@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    [t] = file.read.int(lim.t).eoln
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln

    [] = file.read.eof
```

The `eof` here is the end of file: remember to read it as well! Observe how the left side is always enclosed in a list, even if it's a single variable or if it's empty. Don't worry about the first three lines of the function: what's important is how the input is read.

Note how the limits on `t` and `n` are magically checked when we do `int(lim.t)` and `int(lim.n)`. However, as we noted earlier, we still have to check that `n` is one of 1, 2, 3, 69, 420 for the first subtask. To do this, we can use the function `ensure`, which is like `assert` in C++:

```python
@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    [t] = file.read.int(lim.t).eoln
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln
        if subtask == '1':
            ensure(n == 1 or n == 2 or n == 3 or n == 69 or n == 420)

    [] = file.read.eof
```

Put it all together and we've got our validator!

```python
from sys import *
from kg.validators import * ### @import

subtasks = {
    '1': {},
    '2': { 'n': -10**3 < +Var < 10**3 },
    '3': { 'n': -10**5 < +Var < 10**5 },
}

bounds = {
    't': 1 <= +Var <= 10**5,
    'n': -10**5 < +Var < 10**5,
}

@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    [t] = file.read.int(lim.t).eoln
    for cas in range(t):
        [n] = file.read.int(lim.n).eoln
        if subtask == '1':
            ensure(n == 1 or n == 2 or n == 3 or n == 69 or n == 420)

    [] = file.read.eof

if __name__ == '__main__':
    subtask = argv[1] if len(argv) > 1 else None
    if subtask == '--detect-subtasks':
        print(*detect_subtasks(validate_file, stdin, subtasks))
    else:
        validate_file(stdin, subtask=subtask)
```

## The KompGen generator model

In the KompGen model, a generator is a program takes several parameters for input, and outputs something. This output is passed through the *formatter*, which takes the output and prints it to a file according to the input format. Then the *testscript* calls the generators several times.

Let me illustrate with a simple example. Here's a generator that takes two integers, `T` and `N`, and outputs `T` random integers from `1` to `N`, which is saved in a file called `gen_random.py`. You can ignore the header and the footer for now, just focus on the function `gen_random`:

```python
from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

def gen_random(rand, *args):
    T, N = map(int, args[:2])
    res = []
    for cas in range(T):
        res.append(rand.randint(1, N))
    return res

if __name__ == '__main__':
    write_to_file(print_to_file, gen_random, argv[1:], stdout)
```

<!-- TODO change to new write_to_file format, same with all the other files -->

Note that `gen_random` doesn't actually write to the file, it just outputs the integers to be written in the file. The output of `gen_random` will be something like `[5, 10, 2]`. The actual writing is done by the **formatter**, which is saved in a file called `formatter.py`:

```python
def print_to_file(file, cases):
    print(len(cases), file=file)
    for n in cases:
        print(n, file=file)
```

Here, the output of the function `gen_random` is passed as the variable `cases`. So if `gen_random` outputs `[5, 10, 2]`, the function `print_to_file` would print
```
3
5
10
2
```

Recall that our generator is saved in a file called `gen_random.py`. If we want to use it to generate 3 integers between 1 and 10, we'd call it with:

```bash
$ gen_random.py 3 10 > tests/000.in
```

But often you want to call `gen_random.py` multiple times, with different values of `T` and `N`. So you'd want to do do something like

```bash
$ gen_random.py 3 10 > tests/000.in
$ gen_random.py 10 1000 > tests/001.in
$ gen_random.py 10 5000 > tests/002.in
$ gen_random.py 5 10000 > tests/003.in
```

This is a bit of a hassle, so there is a file that does this automatically. This file is called the **testscript**, which is saved in a file called `testscript`. The equivalent of the above would be:

```bash
gen_random 3 10 > $
gen_random 10 1000 > $
gen_random 10 5000 > $
gen_random 5 10000 > $
```

Note how there's no `.py` any more. Also note how we use a `$` instead of specifying the test case numbers manually, which is way more convenient. To recap:

- The **generator** generates a test case's data.

- The **formatter** takes the data and prints it to an input file.

- The **testscript** has a bunch of commands for running the generators.

## My first generator

Let's go back to the problem Mystery Function. For the sake of demonstration, we're going to make generators that output purely random input, which should be strong enough data for this very simple problem.

Let's decide that our generators will return a list of integers, one integer for each test case. Now that we've decided what our generators will return, we can write the formatter, which is the first thing we write when making test cases. Open `formatter.py` and change it to this:

```python
def print_to_file(file, cases):
    print(len(cases), file=file)
    for n in cases:
        print(n, file=file)
```

You may want to keep this file open in your text editor so you can refer to it when writing the generator. You can change the name of the function `print_to_file` if you want, but I recommend not doing so.

Rename `gen_random.py` to `gen_subtask1.py`. This file will generate the input for subtask 1. By KompGen convention, all generators must begin with the prefix `gen_`.

Open the new file `gen_subtask1.py`. Let's decide that it will take one integer for input, `T`, the number of test cases. Let's write the main function that will generate the integers:

```python
from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

def gen_subtask1(rand, *args):
    T = int(args[0])
    res = []
    for cas in range(T):
        res.append(rand.choice([1, 2, 3, 69, 420]))
    return res

if __name__ == '__main__':
    write_to_file(print_to_file, gen_subtask1, argv[1:], stdout)
```

The line `T = int(args[0])`, takes in the integer `T` from the input. If you want to take multiple inputs, you can write something like `a, b, c = map(int, args[:3])`, making sure to change `3` with the number of inputs.

The line `res.append(rand.choice([1, 2, 3, 69, 420]))` appends a randomly chosen number from `[1, 2, 3, 69, 420]` to `res`. For randomness, you can use any function in [Python's random module](https://docs.python.org/3/library/random.html), but you have to remember to prefix it with `rand.`.

Note how in the last line, we changed `gen_random` to `gen_subtask1`, which is the name of the function that we wrote.

Now, open `testscript`. Remove everything and replace it with the single line

```bash
gen_subtask1 100000 > $
```

Now, let's make our test cases! With your terminal opened in the `mystery-function` folder containing all of our files, run the command

```bash
$ kg make inputs
```

It will throw an error. Thankfully, KompGen has very nice errors, and it tells us exactly what's wrong:

```
kg.script.testscripts.TestScriptError: Couldn't find program gen_subtask1
(from testscript). It should be in 'generators'
```

The issue here is that we haven't updated `details.json`. Remember that KompGen doesn't know a program exists unless it's in `details.json`, so whenever we make a new generator, we have to update that file. Open the file `details.json` and change `gen_random.py` to `gen_subtask1.py`:

```json
"generators": [
    "gen_subtask1.py"
],
```

Now, run the command `kg make inputs` again. It should make a single file `tests\000.in`. If you open it, you should see 

```
100000
3
420
1
2
3
3
69
420
3
...
```

### A note on reproducibility

Now wait a minute. If the test cases are being generated randomly, how do I know exactly what your file looks like? This is because the same generator and the same argument list, will always produce the same output. So if your testscript looks like:

```bash
gen_subtask1 100000 > $
gen_subtask1 100000 > $
gen_subtask1 100000 > $
```

then `kg make inputs` will just make the same input file three times. This is important so that the same KompGen source files always produce the same output, for consistency. (This is also why you should always use random functions by prefixing them with `rand.`, rather than using `from random import *`.)

To make the outputs actually different, we can just pass extra arguments:

```bash
gen_subtask1 100000 ignored1 > $
gen_subtask1 100000 ignored2 > $
gen_subtask1 100000 ignored3 > $
```

The generators ignore any extra arguments. But because the arguments are changed, a different random seed is generated, and the outputs are also changed.

## Another generator and sample input

Let's write the second generator, which we'll use for subtasks 2 and 3. It will take two inputs, `T` and `N`, where `T` is the number of test cases and `N` is the maximum absolute value of `n`.

To make sure the test cases are different, we're going to use the function `rand.shuffled`, which shuffles a list and returns a new list. (If you're familiar with `rand.shuffle`, this is slightly different, because `shuffle` shuffles an existing list and doesn't return anything. Think about the difference between `sorted(a)` and `a.sort()`.)

Duplicate the file `gen_subtask1.py`, and rename the duplicate `gen_random.py`. Since we made a new file, let's modify `details.json` to have:

```json
"generators": [
    "gen_subtask1.py",
    "gen_random.py"
],
```

Now open `gen_random.py`. Let's write it:

```python
from sys import *
from kg.generators import * ### @import
from formatter import * ### @import

def gen_random(rand, *args):
    T, N = map(int, args[:2])
    res = rand.shuffled(range(-N+1, N))
    while len(res) < T:
        res.append(rand.randint(-N+1, N-1))
    return res[:T]

if __name__ == '__main__':
    write_to_file(print_to_file, gen_random, argv[1:], stdout)
```

Again, since we changed the name of the function to `gen_random`, we also changed the last line to have `gen_random` as well. Then we open `testscript`, and change it to:

```bash
gen_subtask1 100000 > $
gen_random 100000 1000 > $
gen_random 100000 100000 > $
```

Now we run `kg make inputs` again. Inspect the inputs yourself to see if it has what you want. If not, then you can always edit the generators and testscript and run `kg make inputs` until you get what you want. This is the typical cycle when making test cases.

Finally, we write the sample input. Since this is written by hand, we won't use a generator for this. Instead, open the file `sample.in`, which should already exist, and change it to:

```
1
1
```

Then open `testscript` and change it to:

```bash
! cat sample.in > $
gen_subtask1 100000 > $
gen_random 100000 1000 > $
gen_random 100000 100000 > $
```

The `!` at the beginning of the line means "run this command as is". So the first line here takes the contents of `sample.in`, and the testscript puts it in the first input file. This is what the command `cat` does. If you don't know what `cat` does, for now, it's enough to remember that if you want to make input manually, use the format `! cat manual_input.in > $`.

Note that sample inputs should come before any of the other inputs in the problem. And with that, we're done making the generators!

## Writing the model solution and making all

The remaining steps are pretty easy: writing the model solution and the checker. The model solution is pretty short for this problem. Open `solution.py` and replace it with

```python
for cas in range(int(input())):
    n = int(input())
    if n >= 1:
        print(n**3 + n**2 + n + 1)
    else:
        print("NONE")
```

And then we choose the checker. In fact, for this problem, we don't have to do anything, since we're going to use the default checker. The default checker simply checks if the contestant's output is exactly the same as the model solution's output, with some leniency with whitespace.

So we're actually done! Run the command

```bash
$ kg make all
```

and watch the magic happen. KompGen will use your testscript and generators to make the inputs for the problem, then use the model solution to generate the correct outputs, and finally use the validator to detect subtasks.

You can inspect the generated input and output yourself in the folder `tests`: the corresponding output to `000.in` is `000.ans`, for example. You can also inspect the detected subtasks by opening the file `subtasks.json`, which should look like:

```
[
    [0, 1, [1, 2, 3]],
    [2, 2, [2, 3]],
    [3, 3, [3]]
]
```

The second line means tests `0` through `1` are in subtasks `1`, `2`, and `3`. Something like `[10, 22, [2, 4]]` would mean tests `10`, `11`, `12`, and so on up to `22`, are all in subtasks `2` and `4` only, and not in any other subtask.

## Sharing your work

Suppose you want to upload your problem to Polygon, which is the platform NOI.PH currently uses to develop problems. After running `kg make all`, run the command

```bash
$ kg kompile
```

This should make a folder called `kgkompiled`. In it should be the folder `pg`. We will use this folder when uploading to Polygon.

First, login or register to Polygon. At the toolbar on top, click New Problem. Name the problem `mystery-function`, and then press Create. Then find the problem `mystery-function` in your list of problems, and click Start.

In the toolbar above, click Statement, choose English as a language, and press Create. Before typing anything, scroll down and check Show section 'Scoring'. Then fill in the problem statement by copying and pasting the fields in `statement.tex`, adding the name of the problem, the statement under Legend, the input and output formats, the constraints under Scoring, and the sample explanation under Notes. Then hit Save.

In the toolbar above, click Files. In the Source Files section, click Add Files, then Choose Files. Go to the folder `mystery-function/kgkompiled/pg` we have from earlier, and upload `gen_subtask1.py`, `gen_random.py`, and `validator.py`. Then click Add Files. (*Do not upload the files in `mystery-function`.* You always want to upload the files in `kgkompiled/pg`.)

In the toolbar above, click Checker. Select `ncmp.cpp` as the checker, and click Set checker. Then click Validator in the toolbar, select `validator.py`, and click Set validator.

In the toolbar above, click Tests. First you have to add in any tests that you do `! cat` in testscript, since Polygon doesn't support that. To add a test manually, click Add Test. Paste in the data in `sample.in`, then check Use in statements, and hit Create.

After making the sample test, click Tests in the above toolbar again. Open `testscript` and paste its contents below Script:, then remove any lines beginning with `!`. Click Save Script. It is in the Tests tab that we can also set the scoring, but we won't do so now.

In the toolbar above, click Solution files. Click Add Solutions, then Choose Files. Upload `solution.py`, then click Add Files. To add other users who can see the problem, click Manage access in the above toolbar.

*Finally,* look at the lowest box in the right sidebar. Hit Commit Changes, and add a commit message. You probably want to check the Don't send email notification checkbox, which is somewhat customary in the NOI.PH Scientific Committee to avoid email spam. Then hit Commit!

<!-- TODO screenshots? -->

When sharing a problem you made in KompGen to others, it's typical to not include the `tests/` folder and the `kgkompiled/` folder, because these can be generated from the KompGen source files anyway. You can also delete these folders if you want to save space.


# Sharing Chocolates 7

Now, let's set the problem [Sharing Chocolates 7](https://www.hackerrank.com/contests/noi-ph-2019-finals-practice/challenges/sharing-chocolates-7). We'll get some more practice using KompGen, write a slightly more advanced validator, and talk about the evils of floating point.

## Statement and initialization

Here's the `statement.tex` we'll be using:

```tex
Title: Sharing Chocolates 7: The Force Equals Mass Times Acceleration  
Slug: sharing-chocolates-7  
Description: ?  
Author: Kevin  


\section{Statement}

Given two integers $F$ and $m$, output $\frac{F}{m}$.


\section{Input Format}

The first line of input contains $t$, the number of test cases.

Each test case consists of a single line containing two space-separated 
integers, $F$ and $m$.


\section{Output Format}

For each test case, output a single line containing a single real number equal 
to $\frac{F}{m}$. Your answer will be considered correct if it is within an 
absolute or relative error of $10^{-6}$ from the correct answer.  

\textit{Note:} Suppose the real answer is $r$, and your output is $s$. Then:

\begin{itemize}

\item The \textbf{absolute error} is defined as $|r - s|$.

\item The \textbf{relative error} is defined as the smaller number between 
$\frac{|r - s|}{|r|}$ and $\frac{|r - s|}{|s|}$. (If the denominator is $0$,
then we ignore it.)

\end{itemize}


\section{Scoring}

\textbf{For all subtasks}

$1 \le t \le 11111$

$1 \le F, m \le 10^9$

\textbf{Subtask 1} (20 points):

$1 \le F, m \le 5$

The answer is an integer.

\textbf{Subtask 2} (20 points):

$1 \le F, m \le 100$

The answer is an integer.

\textbf{Subtask 3} (20 points):

The answer is an integer.

\textbf{Subtask 4} (20 points):

$1 \le F, m \le 100$

\textbf{Subtask 5} (20 points):

No additional constraints.


\section{Sample Input}

    2
    2 1
    2 3


\section{Sample Output}

    2.000
    0.666666654321


\section{Notes}

For the second case, the exact answer is $0.666666\ldots$ repeating, but the 
given answer, $0.666666654321$, is accepted since the absolute error from the 
correct answer is $< 10^{-6}$.
```

The only thing here that might be a little tricky is the output format. Again, this is just a standard output format copied from one of the NOI.PH problems. When asking for an answer that's a real number, it's typical to ask for it to have a given absolute or relative error, and the typical number is $10^{-6}$.

Like last time, run the command

```bash
$ kg init sharing-chocolates-7 --subtasks=5
```

Then open `details.json`, change the title of the problem to "Sharing Chocolates 7: The Force Equals Mass Times Acceleration", and then get rid of the generated `statement.md` and replace it with `statement.tex`.

## Writing the validator

You can probably figure out how to write most of the validator yourself. The tricky part is checking whether the answer is an integer. As an exercise, try to write the validator for now ignoring this constraint, and compare your answer to mine. Open `validator.py`, maybe referring to the previous tutorial, and try to write the validator.

Ready? Here's the validator I wrote, without the header or footer. Yours might look a little different, but as long as it does the same thing, that's okay:

```python
subtasks = {
    '1': { 'F': 1 <= +Var <= 5, 'm': 1 <= +Var <= 5 },
    '2': { 'F': 1 <= +Var <= 100, 'm': 1 <= +Var <= 100 },
    '3': { },
    '4': { 'F': 1 <= +Var <= 100, 'm': 1 <= +Var <= 100 },
    '5': { },
}

bounds = {
    't': 1 <= +Var <= 11111,
    'F': 1 <= +Var <= 10**9,
    'm': 1 <= +Var <= 10**9,
}

@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    [t] = file.read.int(lim.t).eoln
    for cas in range(t):
        [F, m] = file.read.int(lim.F).space.int(lim.m).eoln

    [] = file.read.eof
```

Now let's check if the answer is an integer. This is just checking if `F % m == 0`, so we can use an `ensure` statement for this. You can do something like

```python
for cas in range(t):
    [F, m] = file.read.int(lim.F).space.int(lim.m).eoln
    if subtask == '1' or subtask == '2' or subtask == '3':
        ensure(F % m == 0)
```

and it would work: this is totally fine. However, the recommended solution is to add another attribute in `bounds` and `subtasks`. Change them to look like

```python
subtasks = {
    '1': { 'F': 1 <= +Var <= 5, 'm': 1 <= +Var <= 5, 'ansint': True },
    '2': { 'F': 1 <= +Var <= 100, 'm': 1 <= +Var <= 100, 'ansint': True },
    '3': { 'ansint': True },
    '4': { 'F': 1 <= +Var <= 100, 'm': 1 <= +Var <= 100 },
    '5': { },
}

bounds = {
    't': 1 <= +Var <= 11111,
    'F': 1 <= +Var <= 10**9,
    'm': 1 <= +Var <= 10**9,
    'ansint': False,
}
```

Here, we added an attribute `'ansint'`, with a default value of `False`, and set it to `True` for the specific subtasks. Now, instead of doing the check `if subtask == '1'` and so on, we can check if `lim` has `ansint` set to `True`:

```python
for cas in range(t):
    [F, m] = file.read.int(lim.F).space.int(lim.m).eoln
    if lim.ansint == True:
        ensure(F % m == 0)
```

This is so that if we change which subtasks have an integer answer in the future, we can just change `subtasks` without having to worry about changing the main function. Put all together, you should have `validator.py` looking like this:

```python
from sys import *
from kg.validators import * ### @import

subtasks = {
    '1': { 'F': 1 <= +Var <= 5, 'm': 1 <= +Var <= 5, 'ansint': True },
    '2': { 'F': 1 <= +Var <= 100, 'm': 1 <= +Var <= 100, 'ansint': True },
    '3': { 'ansint': True },
    '4': { 'F': 1 <= +Var <= 100, 'm': 1 <= +Var <= 100 },
    '5': { },
}

bounds = {
    't': 1 <= +Var <= 11111,
    'F': 1 <= +Var <= 10**9,
    'm': 1 <= +Var <= 10**9,
    'ansint': False,
}

@validator()
def validate_file(file, subtask=None):
    lim = Bounds(bounds) & Bounds(subtasks.get(subtask))

    [t] = file.read.int(lim.t).eoln
    for cas in range(t):
        [F, m] = file.read.int(lim.F).space.int(lim.m).eoln
        if lim.ansint == True:
            ensure(F % m == 0)

    [] = file.read.eof

if __name__ == '__main__':
    subtask = argv[1] if len(argv) > 1 else None
    if subtask == '--detect-subtasks':
        print(*detect_subtasks(validate_file, stdin, subtasks))
    else:
        validate_file(stdin, subtask=subtask)
```

And now let's move on to the next step: generators!

## Test planning and writing generators

Let's talk about **test planning**. 

<!-- the sample input -->
<!-- the all-possible generator -->
<!-- the stresses -->
<!-- the random cases generator -->

## Writing the model solution and making all

<!-- evils of floating point -->
<!-- super-accurate model solution -->
<!-- standard float checker -->

## Compiling and uploading

<!-- some more detail about kgkompile -->
<!-- talk about polygon's standard checkers -->


# Totally Not Robots

<!-- by now, you should already be familiar with "the standard checklist" -->
<!-- talk about strong testcases -->
<!-- built-in partition function -->


# City Map

<!-- built-in partition function and multi-file generators again -->
<!-- might want to skip if you don't need custom checkers -->
<!-- custom checker model: solution output and judge output -->
<!-- writing the custom checker (being very, very exception-safe) -->
<!-- data maker -->


# Other KompGen features

<!-- ## Multi-file generators -->
<!-- single-file model -->
<!-- lqpl-divmod's generator -->
<!-- distribute model -->
<!-- mystery function's generator -->

<!-- ## Grid generators -->

<!-- ## Built-in graph utilities -->
<!-- graph generators -->
<!-- using utilities for checking graphs -->
