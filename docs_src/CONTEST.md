This assumes you have already written all the problems in your problem set using KompGen, and you would like to easily upload them to contest systems like PC2.  

# PC2

As mentioned in the README, there are two general steps.  

1. Create a `contest.json` file which will contain the details of the contest, including allowed languages and list of problems. A template exists in `examples/templates/contest.json` for you.  

2. Run `kg kontest pc2 path/to/contest.json`. This will create a folder containing, among other things, `contest.yaml`, which can be loaded by PC2.  

We will now explain these in more detail, including additional steps after running `kg kontest`, to ensure a smooth PC2 contest experience.

## contest.json

A `contest.json` file looks like this:

```json
{{ templates/contest.json }}
```

Most fields should be self-explanatory, but here are things to keep in mind:

- The filename can be anything; it doesn't have to be `contest.json`.  

- The `code` field is preferred to not contain any special characters. A folder with that name will be created at the current directory during the next step.

- The `langs` field contains a list of allowed programming languages in the contest. It can be a string denoting the language code name or a dictionary with additional details (like in `cpp` above). The missing fields will have predefined defaults which can be seen in `contest_langs.json`.  

- The `problems` field contains a list of folders representing the problems. Each of these folders must contain a `details.json` file.  


## kg kontest

The next step is to run `kg kontest pc2 path/to/contest.json`. This will create a folder containing, among other things, `contest.yaml`, which can be loaded by PC2.  

A couple of things to keep in mind:

- The `ALLDATA` folder needs to be copied to each judge computer. It must be located in the same absolute path across all jduge computers. (This is a PC2 requirement.) This also means that all judge computers must be identical, including the user name.

    I suggest placing the `ALLDATA` folder in `/home/[user]/[contestcode]/ALLDATA` to make it simple. And then in the admin, go to the *Problems* tab, click *Set Judge's Data Path*, and paste the absolute path to `ALLDATA` there.  

- The command `kg make all` must have been run on each problem. 

- The `*_count` fields are optional.  

An example is provided in `examples/contest.json`. You can run these to test everything:

```bash
cd examples
kg kontest pc2 contest.json
```

This will create a `MAIN` folder from the two example problems.

## Loading to PC2

To load everything to PC2, run the following:

```bash
pc2server --load path/to/CDP/config/contest.yaml
```

Alternatively, run the server normally, and in the admin, go to the *Import Config* tab and load `contest.yaml` there.

If you wish to update an existing PC2 contest, run `kg kontest` again, and then load `contest.yaml` from *Import Config* again. The `--load` method doesn't work in this case.

## Additional settings  

If you wish to hold a practice round, create another `contest.json` file (say `practice_contest.json`) and perform the same steps above. You may load it under a different *Profile*.

There are a couple things that couldn't be set automatically due to PC2 limitations. You'll have to set them manually.

- Update the *Maximum output size* under *Settings*. This is set to a very low 512Kb by default. I suggest 40000Kb. Be sure to click the *Update* button.

- In each problem, a new feature called *Stop execution on first failed test case* sounds useful, but I can't find a way to set it automatically. You'll have to set it manually for now. You don't have to set it for all problems, and you don't have to do it immediately; you may set it while the contest is running, for example if you find judgment too slow due to too many TLEs.

- Passwords of accounts are unchanged from their defaults. (I will make a feature to automate this soon.)

# Other Formats  

Will support soon.
