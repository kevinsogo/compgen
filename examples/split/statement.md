**Statement**  

Given an array, find the longest subsequence consisting of distinct elements. If there are
multiple possible longest subsequences, any one will be accepted.  

**Input Format**  

The first line of input contains $t$, the number of test cases. The test cases themselves
are described in the following lines.

The first line of each test case contains a single integer $n$ denoting the length of the
array. The second line contains $n$ space-separated integers $A_1, A_2, \ldots, A_n$
denoting the elements of the array.

**Constraints**  

$1 \le T \le 10^5$  
$1 \le n \le 10^5$  
The sum of the $n$s in a single file is $\le 5\cdot 10^5$  
$-10^9 \le A_i \le 10^9$  

**Subtask 1**: $n \le 10$  
**Subtask 2**: $n \le 1000$  
**Subtask 3**: No additional constraints  

**Output Format**  

For each test case, output two lines. The first line must contain a single integer $m$
denoting the length of the longest subsequence consisting of distinct elements. The second
line must contain $m$ space-separated integers $B_1, B_2, \ldots, B_m$ denoting a longest
subsequence of the array.  

There may be multiple valid answers; any one will be accepted.

**Sample Input**  

    1
    6
    3 1 4 1 5 -9265

**Sample Output**  

    5
    3 4 1 5 -9265
