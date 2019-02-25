This assumes you have already written all the problems in your problem set using KompGen, and you would like to easily upload them to contest systems like PC2.  



# PC2

As mentioned in the README, there are two general steps.  

1. Create a `contest.json` file which will contain the details of the contest, including allowed languages and list of problems. A template exists in `examples/templates/contest.json` for you.  

2. Run `kg kontest pc2 path/to/contest.json`. This will create a folder containing (among other things) `contest.yaml`, which can be loaded by PC2.  

We will now explain these in more detail, including additional steps after running `kg kontest` to make sure your PC2 contest runs smoothly.

*Note:* As of now, for `checker`s, only KompGen-using python programs are supported. (Will change in the future.)


## contest.json

A `contest.json` file looks like this:

```json
{{ templates/contest.json }}
```

Most fields should be self-explanatory, but here are things to keep in mind:

- The filename can be anything; it doesn't have to be `contest.json`.  

- The `code` field is preferred to not contain any special characters. A folder with that name will be created later.

- Each entry in the `langs` field (list of allowed programming languages) can be a string denoting the language code name or a dictionary containing additional details (like in `cpp` above). The missing fields will have predefined defaults which can be seen in `contest_langs.json`.  

- The `problems` field contains a list of folders representing the problems. Each of these folders must contain a `details.json` file.  

- The `*_count` fields are optional.  

- `judge_count` can be replaced by `judges` which should be a list of judge names. The same is true with the other `*_count` fields.

- The `teams` field is also a bit special: you can group teams/contestants by university/school. See `examples/contest.json` for an example.

- The `teams`, `judges`, etc., fields can also contain a string pointing to a separate `.json` file which contains the list. This is useful if you want to pregenerate them with a different program.

## Compiling to PC2-readable format

The next step is to run `kg kontest pc2 path/to/contest.json`. This will create a folder `kgkompiled/[contestcode]/`. It will contain (among other things) `contest.yaml`, which can be loaded by PC2.  

A couple of things to keep in mind:

- PC2 requires absolute paths in its configuration, so it is highly recommended to pass the `--target-loc` option. This specifies where the contest folder will eventually end up in the admin and judge computers. The contest folder (`[contestcode]/`) will still be generated in `kgkompiled/`, but it will be configured as if it will eventually be placed in `--target-loc` when it is loaded by PC2.

    You can also specify the `"target_loc"` in `contest.json`.  

    I suggest something simple like `/home/[user]/` for the `target_loc`.  

    You then need to place the `[contestcode]/` folder in `target_loc`.
    
    *Note:* It must be located in the same absolute path across all judge computers. This is a PC2 requirement. This also means that all judge computers must be identical, including the name of the current user.

- `kg kontest` expects that `kg make all` has been run for every problem. If you want to force run `kg make all` across all problems, pass the `--make-all` option to `kg kontest`.

A working example is provided in `examples/contest.json`. You can run this to test it:

```bash
$ kg kontest pc2 examples/contest.json   # add --make-all if you want
```

This will create the folder `kgkompiled/EXAMPLECONTEST` from the two example problems.



## Loading to PC2

To load everything to PC2 the first time you run a server, run the following:

```bash
$ bin/pc2server --load path/to/[contestcode]/CDP/config/contest.yaml
```

Alternatively, run the server normally, and in the admin, go to the *Import Config* tab and load `contest.yaml` there.

If you wish to update an existing PC2 contest, run `kg kontest` again, and then load `contest.yaml` from *Import Config* again. The `--load` method cannot be used to update.

If you wish to use PC2 Profiles, you can load each one using the *Import Config* tab, per profile. 


## Additional PC2 settings  

There are a couple of other options that I couldn't find a way to set automatically. You'll have to set them manually for now. You need to be an admin to do them.

- Update the *Maximum output size* under *Settings*. This is set to a very low 512Kb by default. I suggest 40000Kb. Be sure to click the *Update* button.

- In each problem, there's also a new feature called *Stop execution on first failed test case* which sounds very useful. You don't have to set it for all problems, and you don't have to do it immediately; you may set it while the contest is running, for instance if a particular problem seems to be attracting too many TLEs.

- Good random passwords have been created for all accounts. To upload them, go to the *Accounts* tab, click *Load*, and select the `accounts_{contestcode}.txt` file.
    
    *Note:* The `logins_*.html` files contain the same passwords but in printable formats which can be distributed to the teams. (Keep them safe!)


## Practice contest

If you wish to hold a practice round, create another `contest.json` file (say `practice_contest.json`) and perform the same steps above. Give it a different contest code. (You may load it under a different PC2 *Profile*.)


## Additional PC2 notes  

Unfortunately, PC2 is quite buggy, so I would like to mention a few important ones here. These don't have anything to do with KompGen but I'm including it here anyway because I'm nice.

- Most of the time, PC2 v9.6.0 cannot handle submissions which do not read the whole input file completely. (It will issue an error like "broken pipe" or "stream closed".) You will most likely encounter these types of problems during the practice round since contestants will be testing the system. In this case, it is better to run the submission manually. Just be sure to read the code first to make sure it isn't doing anything dangerous like deleting folders.  

- The default compile and run commands per language are based off of PC2's defaults, but these defaults don't seem to properly handle filenames with spaces in them, like `Problem A.cpp`. You might need to update the compile and run commands per language.  (If you find cross-platform-compatible versions of these commands, please write them in `contest_langs.json` and issue a merge request to KompGen!)
    
    You may also want to tell the contestants to not use spaces/special characters in their filenames.

- For some reason, PC2 uses `a.txt` as the filename that contains the output data, so a submission overwriting the contents of the file `a.txt` might get judged as "Yes" purely because `a.txt` is being overwritten! (Huge security issue, I know.) For this, I suggest reading each submission that is judged "Yes" if they're reading off/writing to a file, and if so, running it manually as well.

    You may also want to tell contestants to read from stdin and print to stdout, and that reading from/writing to a file is not allowed.

- I don't know if this bug still exists in v9.6.0, but in previous versions, PC2 cannot efficiently handle output with very long lines, say 1 million characters in a single line. I think it is the Java GUI that can't handle it (although it can handle a million short lines just fine). In that case, you may want to judge this problem manually, or simply ensure that output lines in your problem are not that long. (Again, not sure if the bug still exists.)

- Although I attempt to set it automatically, the "scoreboard freeze" feature of PC2 doesn't seem to work. Please watch out if this is the case, and if so, just shut down the scoreboard accounts manually at the moment you want to freeze the scoreboard.

- To make manual testing easier, I suggest installing KompGen in the judge computer so that you have access to `kg gen/test/run`. (The data is available in `ALLDATA/[problem_code]/` and custom checkers are available at `CDP/config/[problem_code]/output_validators/` if you need them. You may need them as the `-i`, `-o` and `-jf` arguments.)  

- I don't know of any way to set the following things, either manually or automatically: runtime memory limit, compile time limit, compile memory limit. Please tell me if you know. Thanks!


# Other Formats  

Will support soon.



