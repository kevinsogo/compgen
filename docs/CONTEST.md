<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE. -->
<!-- Edit docs/src/CONTEST.md instead, then run 'docs/src/makedocs'. -->


This assumes you have already written all the problems in your problem set using KompGen, and you would like to easily upload them to contest systems like PC2 and DOMjudge.  

As mentioned in the README, there are two general steps.  

1. Create a `contest.json` file which will contain the details of the contest, including allowed languages and list of problems. A template exists in `examples/templates/contest.json` for you.  

2. Run `kg kontest [format] path/to/contest.json`. This will create a folder containing configuration files, test data, etc., formatted so that they can be loaded by the contest platform.  

We will now explain these in more detail, including additional steps after running `kg kontest` to make sure your contest runs smoothly with your chosen contest platform.

*Note:* As of now, for `checker`s, only KompGen-using python programs are supported. (Will change in the future.)



# Contest configuration file

The first step is to create a contest configuration file, e.g., `contest.json`. A `contest.json` file looks like this:

```json
{
    "title": "My Cool Programming Contest",
    "code": "COOLCONTEST",
    "duration": "5:00:00",
    "scoreboard_freeze_length": "01:00:00",
    "langs": [
        "java",
        "c",
        {
            "lang": "cpp",
            "compile": "g++ -O2 -std=gnu++14 -o {filename_base}.exe {filename}"
        },
        "python2",
        "python3",
        "pypy2"
    ],
    "problems": [
        "path/to/addition",
        "path/to/split"
    ],
    "site_password": "password_to_contest",
    "team_count": 11,
    "judge_count": 4,
    "admin_count": 3
}
```

Most fields should be self-explanatory, but here are things to keep in mind:

- The filename can be anything; it doesn't have to be `contest.json`.  

- The `code` field is preferred to not contain any special characters. A folder with that name will be created later.

- Each entry in the `langs` field (list of allowed programming languages) can be a string denoting the language code name or a dictionary containing additional details (like in `cpp` above). The missing fields will have predefined defaults which can be seen in `contest_langs.json`.  

- The `problems` field contains a list of KompGen folders representing the problems. Each of these folders must contain a `details.json` file.  

- The `*_count` fields are optional.  

- `judge_count` can be replaced by `judges` which should be a list of judge names. The same is true with the other `*_count` fields.

- The `teams` field is also a bit special: you can group teams/contestants by university/school. See `examples/contest.json` for an example.

- The `teams`, `judges`, etc., fields can also contain a string pointing to a separate `.json` file which contains the list. This is useful if you want to pregenerate them with a different program.

<!-- TODO document more of the fields -->



# PC2

PC2 has been used in a couple of ICPC contests. Thus, it mainly supports ICPC-style contests, i.e., binary problems.


## Compiling to PC2-readable format

After writing a `contest.json`, the next step is to run:

```bash
$ kg kontest pc2 path/to/contest.json
```

This will create a folder `kgkompiled/[contestcode]/`. It will contain (among other things) `contest.yaml`, which can be loaded by PC2.  

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

- Related to this, PC2 can't seem to handle it if there are hundreds of files and each test case is processed (run+validate) very quickly. At some point, it just stops, and you have to restart the judgment. I don't know of any fixes to this.

- The default compile and run commands per language are based off of PC2's defaults, but these defaults don't seem to properly handle filenames with spaces in them, like `Problem A.cpp`. You might need to update the compile and run commands per language.  (If you find cross-platform-compatible versions of these commands, please write them in `contest_langs.json` and issue a merge request to KompGen!)
    
    You may also want to tell the contestants to not use spaces/special characters in their filenames.

- I don't know if this bug still exists in v9.6.0, but in previous versions, PC2 cannot efficiently handle output with very long lines, say 1 million characters in a single line. I think it is the Java GUI that can't handle it (although it can handle a million short lines just fine). In that case, you may want to judge this problem manually, or simply ensure that output lines in your problem are not that long. (Again, not sure if the bug still exists.)

- Although I attempt to set it automatically, the "scoreboard freeze" feature of PC2 doesn't seem to work. Please watch out if this is indeed the case, and if so, just shut down the scoreboard accounts manually at the moment you want to freeze the scoreboard.

- To make manual testing easier, I suggest installing KompGen in the judge computer so that you have access to `kg gen/test/run`. (The data is available in `ALLDATA/[problem_code]/` and custom checkers are available at `CDP/config/[problem_code]/output_validators/` if you need them. You may need them as the `-i`, `-o` and `-jf` arguments.)  

- I don't know of any way to set the following things, either manually or automatically: runtime memory limit, compile time limit, compile memory limit. Please tell me if you know. Thanks!



# DOMjudge

DOMjudge has been used in several ICPC world finals and several ICPC regionals. Thus, it mainly supports ICPC-style contests, i.e., binary problems.

## Compiling to DOMjudge-readable format

After writing a `contest.json`, the next step is to run:

```bash
$ kg kontest dom path/to/contest.json
```

This will create a folder `kgkompiled/[contestcode]/`. 

After doing this, and after getting the domserver and at least one judgehost working, and logging in as an admin, here are the steps you should take:


### A. Prepare the accounts

I recommend removing the default contest/problem/affiliation entries (and also the team `exteam`) to make things simpler. (Don't remove the DOMjudge team and the admin and judgehost accounts!)

1. Ensure that the admin account is attached to a team.

    - The easiest way to do this would be to add the admin as a member of the default DOMjudge team. (Edit the admin User, add the "Team Member" role, and set the Team to "DOMjudge").

2. Import `accounts.tsv` via "Import / export" (under "Administrator").

3. DON'T import `teams.tsv`! They don't contain the passwords. Instead, follow the instructions printed by `kg kontest dom`, i.e., use user_team_data.txt to import the team data (including passwords) directly to the database by doing the following:
        
    1. Copy the files `dom_create_teams` and `user_team_data.txt` into the `bin/` folder of your domserver machine. (Note: for reference, this folder is found in the [domserver Docker container](https://hub.docker.com/r/domjudge/domserver/) at `/opt/domjudge/domserver/bin/`)
    
    2. Go to the said `bin/` folder (in the domserver machine), then run `./dom_create_teams < user_team_data.txt`.


### B. Prepare the contest

Unfortunately, the contest config settings cannot be imported into DOMjudge :( So some settings in `details.json` are ignored, and you have to do these manually. (At least the problems can be imported!)

1. Create the contest in "Contest" (under "Before contest"). Set things manually.

2. Update the "Configuration settings" (under "Administrator"). Feel free to choose your own, but I recommend the following:

    - sourcesize_limit: 50 (also update etc/submit-config.h.in)
    - script_filesize_limit: 1000000 (Important!)
    - show_relative_time: Yes
    - show_limits_on_team_page: Yes

3. Configure the languages in "Languages" (under "Before contest").

    - You may want to add `.py` as an extension for Python 3.
    - You may also want to add PyPy 3.
    - I suggest not adding Python 2 (and PyPy 2) since it is at the end of its life span.


### C. Prepare the problems

1. Go to "Executables" (under "Before contest") and upload all zip files in `UPLOADS/UPLOAD_1ST_executables/`.  

2. Go to "Problems" (under "Before contest") and upload all zip files in `UPLOADS/UPLOAD_2ND_problems/`.

    - Be sure to select the correct contest!

    - If this fails, one reason might be because of large test data. See the "other notes" section below.


### D. Verify

Then you're done! You should verify that things went well by doing the following:

1. Go to "Submissions" (under "During contest") and check that all problems had at least one submission from the admin and they all got accepted.

2. Go to "Config checker" (under "Administrator") and check that everything is nice and green. (If not, fix them.)


### Other notes

You can easily do the same process if you're planning on hosting a practice round.

Interactive problem support to come soon. (For now, you can still do it, but you'll have to manually set up the run and compare commands yourself, so KompGen saves you 80% of the work.)

It may happen that DOMjudge doesn't accept some problem because or large test data. In this case, please follow the ["Fine tuning server settings"](https://www.domjudge.org/docs/admin-manual.pdf) section of the [DOMjudge admin manual](https://www.domjudge.org/docs/admin-manual.pdf) to change MySQL settings. `max_allowed_packet` is the most relevant, although you may want to adjust the others as well just to be sure.



# CMS

CMS is the official platform used at the IOI and maintained by the IOI. Thus, it mainly supports IOI-style contests, i.e., non-binary problems.

## Compiling to CMS-readable format

At the moment, it's not possible to add custom Loaders for CMS with an external Python library, so our power to set things up automatically is a bit limited. I'll work on it soon; meanwhile, I've implemented a compiler towards the "Italian format", which, while not perfect, at least helps out a bit.

After writing a `contest.json`, run:

```bash
$ kg kontest cms-it contest.json
```

This will generate the contest problems in Italian format in `kgkompiled/[contestcode]`.  

Please keep in mind though that the Italian format is very limited (acknowledged even by the [official CMS docs](https://cms.readthedocs.io/en/v1.4/External%20contest%20formats.html)), so, as with DOMjudge, a lot of the contest config settings are thrown away.



# Other Formats  

Will support soon.



