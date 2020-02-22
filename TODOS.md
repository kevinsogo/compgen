 Important  

- Write unit tests.  

- Handle non-kg checker for pc2 contest configuration.

- Support pc2 input validator. (right now I can't get it to work. email thread with PC2 team.)

- Support more formats: Kattis, CodeChef.  


# To consider  

This includes some disorganized ideas, TODOs, notes...

- Allow running several solutions at once.  

- For Polygon checkers, maybe print specific message for verdict

- Author/s fields.

- Request CMS folks to allow external loaders.

- Stronger args support for generators.

- maybe pass newline='' in checker streams?

- Flag to use a custom python3 script. Useful in case some generators use later python features not available in the latest pypy3.

- Chef: on kg kompile, create a script that uploads. Alternatively, kg chefupload (or something similar).

- On kg kompile pg, on ignored testscript lines, store them in a separate folder/archive so that they can upload easily.

- Separate the kg-cli from the @importable kg's, and make the latter freezable. Maybe have kg init freeze them and have a kg init --update to update the files. have them connect to version number? this is so that we can make backwards-incompatible changes.

- On versioning and backwards compatibility: only the @import-able functions need to be thoroughly backwards compatible. make a mechanism there that imports specific versions.

- Properly delete contest files in kgkompiled/ when running `kg kompile` again.

- Allow a program to be under "testscript" in details.json. It will then generate the actual testscript.

- Allow to mark lines in the testscript as "to-upload-manually", perhaps with a special first/last token like ":". Require them to be the first few files if polygon (on kg kompile). "!" are automatically manual-upload and thus required to be the first few files.

- Add something like Jinja support for testscript?

- kg run without -i

- DOM, important: can't upload files because of max packet thing. fix it.

- more efficient handling of regex and .token. 

- kg.formatters with a @formatter() decorator. it passes a "print" function.

- Make +Var non-sticky; perhaps "freeze" it when it is passed through validator.

    probably: with +Var (or something similar)

    probably wouldn't hurt to freeze them anyway again.

- DOM: Importing contest info directly to the database (similar to user_team_data.txt). /api/doc has models at the bottom, which is helpful.

- Check if pc2 still works

- Consider: Rename `details.json`? `kg_problem_config.json` or something.

    - We can have the name "details.json" written in `__init__.py` or something

- Print out which lines were skipped when compiling the testscript to a polygon testscript.

- Have "statement" in details.json. It will override global_statements (or join with it; the point is, it has higher priority)

- reorganize `formats.py`, `kg_compile` and `kg_contest`.
    
    - Each contest format must be in its own file/files.
    - Take advantage of inheritance.
    - "Compile a problem".
    - "Compile a problem as part of a contest package". (sometimes, this just delegates to "compile a problem")
    - "Compile a contest".

- labels for Var/Interval objects. (passed through validator(), the labels can be acquired)

- Have `2 <= Var('x') <= 10` and have incompatibility checks when using `&` with different labels?

- Allow setting of problem colors (should be in contest.json, not in details.json)

- Allow overriding of defaults when using Bounds & Bounds. 

    - This has been implemented already, but the following might not be:

    - Add stderr prints about "overriding" when one is not an Interval. Possibly disallow Interval & non-Interval.

- make kg contest work for non-python programs.

- fix: if validator missing, "kg make all" gives "NoneType has no attribute do_compile"

- Add warning in `KGRandom` about shuffling arbitrary collections, especially unordered ones like sets and dicts. It can override `.shuffle` by adding an optional kwarg, `sort`, which is `False` by default but also issues a warning. Add a way to suppress this warning safely.

    - Maybe `.shuffle_sort` ? (also `.shuffled_sorted` and `.shuff_sorted`)

- Implement something similar to `wnext` of testlib. (must be fast)

- Implement 'or' in bounds/`Var` objects, e.g., `(1 <= +Var <= 100) | (200 <= +Var <= 300)`.  

- `kg make` Warn when test cases are identical. Hash the files and compare hashes only.

- Rename `valid_subtasks` to just `subtasks`. (need backwards compatible)

- Copy statement in dom/problem.tex.j2

- Possibly use HJSON (or something) for config files, not pure JSON.

- Find inspiration from jngen

- Add "stress test" feature; run a given generator multiple times, and stop when a certain number of incorrect answers is detected (default 1).

    - This generator must be able to ignore extra arguments (meant for changing seed)

    - On --help, use "stop when it fails". (just introduce "--fail-threshold" or something as a normal arg.)

- Implement polygon-compatible partial scorer. The behavior should be equivalent to testlib `quitp(_pc(score-16))`
    

    - Some links:

        google: partial scoring codeforces polygon
        google: quitp _pc site:codeforces.com
        https://codeforces.com/blog/entry/47523
        https://codeforces.com/blog/entry/48241
        https://codeforces.com/blog/entry/59886
        https://codeforces.com/blog/entry/63042
        https://codeforces.com/blog/entry/18426
        https://codeforces.com/blog/entry/18455
        https://codeforces.com/blog/entry/18431
        https://codeforces.com/blog/entry/51019
        https://codeforces.com/blog/entry/59886


- Add "pc2" kg kompile and add the yaml writing for a task there

- Add "cms" format and write own Loader (compgen-cms). Notes:

        kg kompile cms:
            creates kgkompiled/cms/ and all its stuff
            also the zipped version for easy portability

            kgkompiled/cms will have:
                checker (shebanged python3 checker). It must be exactly "checker".
                "grader.*" will be copied if it is in other_programs

            so it makes the kgkompiled/cms/ folder
            it makes a json file to make things easy to read
                files to load
                config options
            it also makes kgkompiled/cms/tests.zip
            it also makes kgkompiled/cms/problem_[problemcode].zip
                includes the whole folder (except tests.zip)
        kg contest cms:
            creates a single zip file or something
            So it makes the kgkompiled/CONTESTCODE/ folder
                just contains the problem_[problemcode].zip files and maybe a json file that contains easy-to-read data
            it also makes kgkompiled/CONTESTCODE.zip
        separate package [not directly included in kg] that reads off the zip files. should be "easy to read" at this point. "compgen-cms"

        compgen-cms will contain the loader. the idea is to make it easily included in judging setups without having to add the whole kompgen library. of course, if we're able to make the installation of kompgen smooth, then we can just use kompgen itself.

- Cleanup kg_contest and kg_compile to be more modular

- Fix margins of \_boxes template again. Should not wrap.

- kg make only a subrange of the cases.

    - suggestion: pass an arg as you would the first arg of a multitest generator.

    - or maybe several args, and they will be "unioned".

    - add "union" operation for a t_sequence

- Fix bugs in `--loc`. Something to do with `.{sep}[something].exe`

- Investigate the [WinError 2] thing happening with C++ solutions on windows.

- Add docs for interactors.

- Study pc2 interactors.

- More context/explanation:

    - generators are supposed to give the same output for a given input. also, seed determined by args

    - Add interactor in explanation.

    - Remove "checker" in README.md

- KompGen interactors (kg.interactors). Extract behavior from testlib interactor. Preliminary experiments:

    - `0 = _ok`
    - `1 = _wa`
    - `3 = _fail`
    - So I guess `2` is parse error, and these are basically the same as checkers.

- Remove unneeded whitespace in html files.

- Support for naming arguments in generators, so that they can be added to argparse.
    
    - maybe extract from positional argument signature?

- Add summaries/reports in kg gen and kg run. (and kg make?)

- Renames... (write_to_file* -> gen_to_file?)

- validator read_while
    
    - Also think about how to unify them, i.e., reduce code duplication as much as possible

- implement or by slightly adjusting "Var" representation. make it a tree. have a method that enumerate all conditions.
    
    - but do consider efficiency too. this could be a bit slow

- Create a more flexible "testscript" that kgkompiles to a polygon-compatible one.
    
    - Perhaps jinja

    - Need to think about what happens to "!" commands. (ignore?)

    - Autonumbers stuff so Polygon is happy

- Annotated fields in details.json for programs and their expected verdicts.
    
    - Similar to polygon.

- Geometry library (`kg.geom.*` or `kg.math.geom.*`.)
    
    - Nice things include random polygon, and random convex polygon given number of sides.

- Use `os.path.normcase` (or something similar) on filenames parsed from details.json and similar places, so it could be interpreted properly in the correct OS.

- "kg template" to generate template validators/checkers/generators

- `@set_validator` and `validate()`.
    
    - `@validator` will become an alias of `@set_validator` and is just used for legacy validators.

    - `validate()` can also be `validate(subtasks=subtasks.keys())`. It detects `--detect-subtasks` (using argparse).  

        - Must not issue error when invalid arguments are found.

    - has an optional argument `file=file`.  

- Use Jinja templating for makedocs

- Improve the seating algorithm. Maybe use some simulated annealing or something? haha

- Use subtasks_files (subtasks.json) for kg test if it exists (and format is kg).

- Autocomplete feels slow. try optimizing

- Use bare *

- Force load subtasks for kg test, otherwise we load from details.subtasks_files

- Enclose "@importables" in blocks and only expose the good functions. Maybe automate this with kg kompile.

    - Or just reformat the kg importables to only expose public functions. So give them their own namespace by putting them in a function, so that it doesn't clash with other namespaces.

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

- don't make the kg checkers strict. use parse_known_args

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

- Allow "pypy3" to be used for PC2 checkers. Maybe an option that can be added in `contest.json`.

- Automatically determine the version of the `python` command, and use it to determine the default execution of `.py` files. (This may require overhauling the `langs.json` format.)

- On kg kompile, add option to remove blank lines and trailing spaces?

- Maybe add a whitespace-sensitive version of checker "tokens"? (checkers)

- "Chain-style" checkers.

    - Need to support strictness levels and options. Default is maximum for validators, and somewhere in the middle for checkers, but individual strictnesses should be toggleable, e.g., "trailing whitespace".

- Utility to change line endings. (maybe some argparse args?)

- Support line endings in multiple platforms.

- Support windows.  

    - e.g., the `/usr/bin/time` call in `programs.py` could maybe be replaced. 

    - A lot of the scripts also rely on Ubuntu command-y things.  

- Use gitlab's "Issues" feature and write these things there instead.  

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

- Make "black magic" its separate package (maybe? lol)

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

- For the graphs module, maybe consider having  `uniform=True` option for tree generation, which guarantees equal probability for all trees? I doubt it's needed, though, and could just take up extra code. Maybe `kg.graphs.generators.uniform_trees.*` so it doesn't have to be included all the time. 

- maybe some add "convex increasing" or something, for generators?
 
- Have `kg.validators.get.*` for the `GET` functionality. Move stuff to `validators/{__init__,get}.py`. In general, split up modules so features can be imported individually, so they don't take up space. Only essential ones go to `/__init__.py`.  
    - This requires generalizing `kg kompile`'s current approach, not too hard I think.

- For uniformity:
    
    - Add @set_generator(...same_options_as_write_to_file...)
    - Add non-decorator versions of checker.
    - Decide on "@set_checker" vs "@checker" (and also @generator)

- Add checks to determine python version in setup.sh ? or a custom script that's called by setup.sh, so it can be run individually?



