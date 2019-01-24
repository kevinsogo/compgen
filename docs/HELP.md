# Important  

- Do something about the fact that Python's `random` module makes no guarantees of reproducibility across implementations and platforms; see [this](https://stackoverflow.com/questions/8786084/reproducibility-of-python-pseudo-random-numbers-across-systems-and-versions).
- Give a better name than "compgen". We can still rename this package while it's early.    
- Ensure that multiple instances of the scripts can be run simultaneously, at least the common ones.

# Others  

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

# To consider  

- Make the `direct_to_hackerrank` command look like:

    ```bash
    direct_to_hackerrank testset_script_file -- validator command -- solution command -- subtasks
    ```

    The idea is that `--` can be replaced by any token not appearing in the validator and solution commands. 

- Convert all scripts to Python in case no one knows (or likes to work with) Bash.

- Use gitlab's "Issues" feature and write these things there instead.  

- Generalize `hr` to any of the supported formats. e.g. `localdata`. `hr` will then be an alias of `localdata hackerrank`, but we will have `poly` = `localdata polygon`, `cc` = `localdata codechef`, `localdata kattis`, `localdata pc2`.  

- Make conversion between different formats seamless. `convert_data polygon hackerrank`, `convert_data hackerrank polygon`. The base format could be in one single folder with `.in` and `.ans` extensions. When uploading to hackerrank, a new script will convert them to hackerrank's zip format (without leaving traces of the `input/` and `output/` folder).

    - Preferably, testing (via `hr`-like scripts) is still possible on all supported formats.


