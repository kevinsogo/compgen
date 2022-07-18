**Statement**  

This is a simulation of the "Ten-Hat Variant without Hearing" problem from Wikipedia:

https://en.wikipedia.org/wiki/Induction_puzzles#Ten-Hat_Variant_without_Hearing

There are $10$ prisoners and $10$ hats. Each prisoner is assigned a random hat, either red or blue, but the number of each color hat is not known to the prisoners. The prisoners are distributed in the room such that they can see the hats of the others but not their own. Now, they must each, simultaneously, say only one word which must be "red" or "blue".

If at least $5$ of the words match the corresponding hat color, they are released.

They can formulate a strategy beforehand. Find a strategy that guarantees winning.

*Note:* Your running time is computed as the *max* of the times consumed by all processes, though this may be different in CMS (sum of CPU times).


**Interaction**  

The program is run on $10$ nodes, each given an ID from $0$ to $9$, given as a command line argument.

The judge first sends, to each node, a line containing a single integer $t$, the number of experiments.

For each experiment, the judge sends a line to each node. To node $i$, it will send a line containing a string of length $10$, the (zero-indexed) $j$th character of which is

- `R` if the $j$th person has a red hat,
- `B` if the $j$th person has a blue hat, or
- `?` if the $j$th person cannot see this hat, i.e., $i = j$.

Each node must then print a line containing a single character, either `R` or `B`, denoting their guess on what their hat color is.

Remember to flush your output!

*Note:* All $t$ experiments will be performed even if the group has already "failed" some of them.


**Constraints**

$1 \le t \le 10^4$
