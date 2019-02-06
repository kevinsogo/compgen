<!-- NOTE TO CONTRIBUTORS: PLEASE DON'T EDIT THIS FILE. -->
<!-- Edit docs_src/CONTEST.md instead, then run './makedocs'. -->


This assumes you have already written all the problems in your problem set using KompGen, and you would like to easily upload them to contest systems like PC2.  

# PC2

As mentioned in the README, there are two general steps.  

1. Create a `contest.json` file which will contain the details of the contest, including allowed languages and list of problems. A template exists in `examples/templates/contest.json` for you.  

2. Run `kg kontest pc2 path/to/contest.json`. This will create a folder containing, among other things, `contest.yaml`, which can be loaded by PC2.  

We will now explain these in more detail, including additional steps after running `kg kontest` to make sure your PC2 contest runs smoothly.

## contest.json

A `contest.json` file looks like this:

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

- The `code` field is preferred to not contain any special characters. A folder with that name will be created at the current directory later.

- The `langs` field contains a list of allowed programming languages in the contest. Each entry can be a string denoting the language code name or a dictionary containing additional details (like in `cpp` above). The missing fields will have predefined defaults which can be seen in `contest_langs.json`.  

- The `problems` field contains a list of folders representing the problems. Each of these folders must contain a `details.json` file.  


## kg kontest

The next step is to run `kg kontest pc2 path/to/contest.json`. This will create a folder containing, among other things, `contest.yaml`, which can be loaded by PC2.  

A couple of things to keep in mind:

- The `ALLDATA` folder needs to be copied to each judge computer. It must be located in the same absolute path across all jduge computers. This is a PC2 requirement. This also means that all judge computers must be identical, including the name of the current user.

    I suggest placing the `ALLDATA` folder in `/home/[user]/[contestcode]/ALLDATA` to make it simple. And then in the admin, go to the *Problems* tab, click *Set Judge's Data Path*, and paste the absolute path to `ALLDATA` there.  

- `kg kontest` expects that the command `kg make all` has been run for every problem. 

- The `*_count` fields are optional.  

- `judge_count` can be replaced by `judges` which should be a list of judge names. The same with the other `*_count`s.

- The `teams` field is also a bit special: you can group teams according to their university. See `examples/contest.json` for an examsple.

A working example is provided in `examples/contest.json`. You can run these to test it:

```bash
cd examples
kg kontest pc2 contest.json
```

This will create a `kgkompiled/EXAMPLECONTEST` folder from the two example problems.

## Loading to PC2

To load everything to PC2, run the following:

```bash
pc2server --load path/to/CDP/config/contest.yaml
```

Alternatively, run the server normally, and in the admin, go to the *Import Config* tab and load `contest.yaml` there.

If you wish to update an existing PC2 contest, run `kg kontest` again, and then load `contest.yaml` from *Import Config* again. The `--load` method doesn't work in this case.

## Additional settings  

There are a couple of other options that I couldn't find a way to set automatically. You'll have to set them manually for now.

- Update the *Maximum output size* under *Settings*. This is set to a very low 512Kb by default. I suggest 40000Kb. Be sure to click the *Update* button.

- In each problem, there's also a new feature called *Stop execution on first failed test case* which sounds very useful. You don't have to set it for all problems, and you don't have to do it immediately; you may set it while the contest is running, for instance if a particular problem seems to be attracting too many TLEs.

- Good random passwords have been created for all accounts. To upload them, log in as an admin, go to the *Accounts* tab, click *Load*, and select the `accounts_{contestcode}.txt` file.
    
    The `logins_*.html` files contain the same passwords but in printable formats which can be distributed to the teams.

## Practice contest

If you wish to hold a practice round, create another `contest.json` file (say `practice_contest.json`) and perform the same steps above. You may load it under a different *Profile*.

# Other Formats  

Will support soon.
