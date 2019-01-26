<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE. -->
<!-- Edit docs_src/HELP.md instead, then run './makedocs'. -->





# Important  

- Write unit tests.  

- Support more formats: PC2, Kattis, CodeChef, DOM?. 



# Others  

- Improve `StrictStream`. Right now, I'm manually buffering 10^5 characters at a time, but I think there has to be a more idiomatic way to buffer.  

- Do something about the fact that Python's `random` module makes no guarantees of reproducibility across implementations and platforms; see [this](https://stackoverflow.com/questions/8786084/reproducibility-of-python-pseudo-random-numbers-across-systems-and-versions). I guess a simple solution would be to copy `random.py`, but this would blow up the sizes of the files in `kgkompiled`.

- Ensure that the scripts work even in path names containing spaces and special characters. 

- Improve the handling of other forms of `import`.

- More error handling in scripts; in general, make them more robust.

- Better error messages. 



# To consider  

- Use gitlab's "Issues" feature and write these things there instead.  

