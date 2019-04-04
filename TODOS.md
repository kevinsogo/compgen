# Important  

- Write unit tests.  

- Handle non-kg checker for pc2 contest configuration.

- Support pc2 input validator. (right now I can't get it to work. email thread with PC2 team.)

- Support more formats: Kattis, CodeChef, DOM?.  


# To consider  

This includes some disorganized ideas, TODOs, notes...

- Allow running several solutions at once.  

- Author/s fields.

- Allow overriding of defaults when using Bounds & Bounds. Add stderr prints about "overriding" when one is not an Interval. Possibly disallow Interval & non-Interval.

- Possibly use HJSON (or something) for config files, not pure JSON.

- Add summaries/reports in kg gen and kg run. (and kg make?)

- Renames... (write_to_file* -> gen_to_file?)

- Create a more flexible "testscript" that kgkompiles to a polygon-compatible one.
    
    - Perhaps jinja

    - Need to think about what happens to "!" commands. (ignore?)

- Annotated fields in details.json for programs and their expected verdicts.

- Allow compilation of a single file. `kg kompile -f`.
    
    - Maybe params for imported packages, like `kg kompile -f [...] -i [... [...]]`.  

- Geometry library (`kg.geom.*` or `kg.math.geom.*`.)
    
    - Nice things include random polygon, and random convex polygon given number of sides.

- Use `os.path.normcase` (or something similar) on filenames parsed from details.json and similar places, so it could be interpreted properly in the correct OS.

- "kg template" to generate template validators/checkers/generators

- `@set_validator` and `validate()`.
    
    - `@validator` will become an alias of `@set_validator` and is just used for legacy validators.

    - `validate()` can also be `validate(subtasks=subtasks.keys())`. It detects `--detect-subtasks` (using argparse).  

    - has an optional argument `file=file`.  

- Use Jinja templating for makedocs, seating and passwords

- Use subtasks_files (subtasks.json) for kg test if it exists (and format is kg).

- Autocomplete feels slow. try optimizing

- Use bare *

- Force load subtasks for kg test, otherwise we load from details.subtasks_files

- Enclose "@importables" in blocks and only expose the good functions. Maybe automate this with kg kompile.

- Add compatibility warning for validators: Don't return 42 since that's the success code for the pc2/kattis format.

- For kg kontest, instead of relpath, "go to directory and run there".

- Allow non-kg formats in `kg kontest`. Its entry in `problems` could basically contain the `details.json`, at least those which are required. 

- study setuptools versioning

- kg-make-checker to return a standalone checker program from !diff.xxx, and that it can receive args. 

- override lang commands on details.json

- Interactive editor for seating arrangements. (maybe, kcvajgf.github.io, also maybe vue.js or something.)

- groupInto -> chunk, as per lodash. Also find other things there.

- Support for stress testing. `kg.stresses`, I guess.

- Export to .tex format, both for Kattis and for `\newproblem{title}{TL}` format.

- Use a YAML library.

- Consider using the Kattis format as the base. (far future backwards-incompatible version.)

- Improve `StrictStream`. Right now, I'm manually buffering 10^5 characters at a time, but I think there has to be a more idiomatic way to buffer.  

- Add option to generate only subranges of the tests, to make it fast.

- Do something about the fact that Python's `random` module makes no guarantees of reproducibility across implementations and platforms; see [this](https://stackoverflow.com/questions/8786084/reproducibility-of-python-pseudo-random-numbers-across-systems-and-versions). I guess a simple solution would be to copy `random.py`, but this would blow up the sizes of the files in `kgkompiled`.

- Ensure that the scripts work even in path names containing spaces and special characters. 

- Improve the handling of other forms of `import`.

- More error handling in scripts; in general, make them more robust.

- Better error messages. 

- Support for graphs in `kg.graphs.{validators,checkers,generators}`

- `"statement"` in details.json, and `statement.md` template. Add recommendation for "pandoc" for conversion between formats. (maybe `kg kompile` automatically converts them to `.tex`, for polygon and kattis/pc2.)

- "masterjudge" support, not just typical binary scoring and subtask scoring. Could be a `master_judge` in details.json which defaults to a subtask/binary grader. 

- More checks against incompatible sets of params (`-F` and `-i`/`-o`.).

- Transparently show which args were used, and which ones were suppressed, and which ones taken from `--details`.

- Implement `-o` only usage of `gen` (and possibly other commands).

- Add options to modify predetermined compile and run for recognized languages. And also add more recognized languages. Currently, the languages are in `langs.json`. Maybe have a `~/.kgconfig` file that overrides these configurations?

- Automatically determine the version of the `python` command, and use it to determine the default execution of `.py` files. (This may require overhauling the `langs.json` format.)

- On kg kompile, add option to remove blank lines and trailing spaces?

- Add natsorted as a python dependency of the kg python package. (?)

- Maybe add a whitespace-sensitive version of checker "tokens"?

- Utility to change line endings.

- Support line endings in multiple platforms.

- Support windows.  

    - e.g., the `/usr/bin/time` call in `programs.py` could maybe be replaced. 

    - A lot of the scripts also rely on Ubuntu command-y things.  

- Use gitlab's "Issues" feature and write these things there instead.  

- Add `### @@ if False { ... }` around bulky docstrings.

- pass stuff via default values, like:

```
@new_case
def make(rand, x=x):
    ...
```

new_case kwargs can still be passed as info.

- Interactors/interactive tasks. (Supported in Polygon, and maybe everywhere except HackerRank?)
    - Python coroutines maybe?

- Import from existing format, not just the I/O but also all other stuff and metadata.

- Warn if two subtasks have exactly the same files.

- Warn absence of @import in things like kg.validator, kg.checker, kg.generators, kg.XXX

- Add more examples. (There are "TODO"s splattered in the docs and everywhere else. grep to find them all)

- Add more templates.

- Future backwards incompatible: use hashlib for hashing purposes (e.g. generating seeds from args)

- use polygon multifile generator [at least support for this]

- for multi-file generators:

    pass the pattern string {1-5,7,8} as argument.  

    we can set up so that we can output through all those files

    allow "[]", "{}" and possibly "none" (add "[]" in-code).

- Add freemarker templating (could be an optional dependency), so we can emulate the Polygon system.

- Cleaning up of kg.generators

        print_to_file(generate(random_cases, *argv[1:]), file=stdout)

        write_to_file(stdout, print_to_file, random_cases, argv[1:])



        for file, cases in zip(filenames(argv[1]), generate(random_cases, *argv[2:])):
            with open(file, 'w') as f:
                print_to_file(cases, file=file)

        write_to_files(argv[1], print_to_file, random_cases, argv[2:])

        write_to_files(filenames(argv[1]), print_to_file, random_cases, argv[2:])




        index = int(argv[1])

        print_to_file(generate(multi_case_lazy(many_cases, distribute, index), *argv[2:]), file=stdout)

        write_to_file(stdout, print_to_file, (many_cases, distribute, index), argv[2:])


- More kg commands, some minor:

        kg blackmagic

        # minor

        # has type checking

        kg set subtasks 1,2,3
        kg set checker checker.py
        kg set checker checker.py "pypy3 checker.py"
        kg set checker checker.java "javac checker.java" "java checker"
        kg set validator
        kg set title
        kg add generators
        kg add other_files
        kg rem generators
        kg add comments

        kg add subtasks 4

        kg add subtasks_files 5 8 1,2,3,4


        kg set -d details.json

        or maybe kg config and kg config --global (sets in ~/.kgconfig), similar to git's "config"


- Implement `@keep` as a command directive and not as a language construct.

- Add kg.formatters if you can think of anything that can be given convenience functions for. TBH though, Python is mighty powerful enough on its own.

- For the graphs module, maybe consider having  `uniform=True` option for tree generation, which guarantees equal probability for all trees? I doubt it's needed, though, and could just take up extra code. Maybe `kg.graphs.generators.uniform_tree.*` so it doesn't have to be included. 

- maybe some add "convex increasing" or something, for generators?
 
- Have `kg.validators.get.*` for the `GET` functionality. Move stuff to `validators/{__init__,get}.py`. In general, split up modules so features can be imported individually, so they don't take up space. Only essential ones go to `/__init__.py`.  
    - This requires generalizing `kg kompile`'s current approach, not too hard I think.

- For uniformity:
    
    - Add @set_generator(...same_options_as_write_to_file...)
    - Add non-decorator versions of checker.
    - Decide on "@set_checker" vs "@checker" (and also @generator)

- Add checks to determine python version in setup.sh ? or a custom script that's called by setup.sh, so it can be run individually?



