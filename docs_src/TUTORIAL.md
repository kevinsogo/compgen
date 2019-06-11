This is a tutorial on how to prepare problems from scratch using KompGen. We'll work through preparing the [NOI.PH 2019 Finals Practice Round](https://hackerrank.com/contests/noi-ph-2019-finals-practice) together, and while doing so, we'll go over many of the features of KompGen that you'll use during problemsetting.


# Installation

I'll assume you have `kg` installed in your system. You can check this by typing `kg` in the termiinal, which should pop up a message like this:
```bash
$ kg
usage: kg [-h] [--krazy]
          {konvert,convert,konvert-sequence,convert-sequence,subtasks,gen,test,run,make,joke,init,kompile,compile,kontest,contest,seating,passwords}
          ...
kg: error: the following arguments are required: main_command
```

If you don't get a message like this, check out the Setup header in the README.

One of the currently weird things about KompGen is that it doesn't have a stable release schedule yet. This means you typically want to pull and reinstall KompGen every time before you work with it.


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

2. The test case is checked if it matches the input format the problem by a program called the *validator*.

3. The contestant's solution is run on this test case, and its output is compared to the model solution by the checker.

This introduces us to our last program: the **validator**. The validator is a program that reads in a file and check if it follows the input format given in the problem statement. It should also be very strict in doing so: it should check that there is no extra whitespace, or even extra blank lines.

You may think that a validator is only necessary when writing problems for Codeforces, but *it's important to write a validator for **every** problem*. This is because in the KompGen model, all test cases made by a generator are run through the validator in order to check if they're valid. This ensures that invalid test data does not appear during the contest.

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

We introduced these five files in the order checker, model solution, generator, validator, and statement. Typically, these files are written *in the reverse order*. This means that the process of making a problem is:

1. Write a clear **statement**.

2. Write a **validator** according to the input format and constraints in the statement.

3. Write **generators** that make the test data for the program. This step is typically the hardest part of problemsetting.

4. Write a **model solution**, and then write a **checker**.

Now that you know how a problem is written, let's set our first problem using KompGen!


# Mystery Function

First, let's set the problem [Mystery Function](https://www.hackerrank.com/contests/noi-ph-2019-finals-practice/challenges/mystery-function).

## Writing the statement



<!-- ## Generators, the testscript, and the validator

In the KompGen model, a generator takes several parameters for input, and outputs test cases. For example, say you have a file called `gen_random.py`, which takes in two integers *T* and *N*, and outputs a file with *T* random test cases, each with size near *N*. This would be called with

```bash
$ gen_random.py 10 100 > 1.in
```

But often you want to call `gen_random.py` multiple times, with different values of `T` and `N`. So you'd want to do do something like

```bash
$ gen_random.py 10 100 > 1.in
$ gen_random.py 10 1000 > 2.in
$ gen_random.py 10 5000 > 3.in
$ gen_random.py 5 10000 > 4.in
```

This is a bit of a hassle, so there is a file that includes instructions for  -->


