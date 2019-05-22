**Statement**  

This is an interactive problem!

The judge has a number in mind: $n$. You need to guess it. You can only perform $m + 1$ actions, each of two types:

- `ask` $x$. The judge responds with the value $x - n$.  
- `answer` $x$. Declare that $n$ is equal to $x$.  

There must be exactly one `answer` action, and it must be the last one. Also, for any action, $|x| \le 10^9$ must hold.  


**Input Format**  

The first line contains an integer $m$. After that, the interaction begins with the solution program doing an action.  

As soon as the judge receives an `answer` action or more than $m$ `ask` actions, the judge exits with a wrong answer verdict. The judge also exits with a wrong answer verdict for any invalid or malformed output.  


**Constraints**  

$1 \le m \le 100$  
$|n| \le 10^9$  


**Sample Interaction**  

```
JUDGE       SOLUTION

5
            ask 42
-27
            ask 420
351
            answer 69
```
