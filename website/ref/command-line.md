# Command line arguments

The subpatch command line tool uses the common argument structure with multiple
arguments and one command. It is the same as other popular tools like `git` or
`docker`. Examples:

    subpatch status
    subpatch add <url> -r <revision>

Here `status` and `add` are commands and `-r <revision>` is an optional
argument.

subpatch uses the [argparse module](https://docs.python.org/3/library/argparse.html) of python.
So the following commands are equivalent:

    subpatch add -r=<revision> <url>
    subpatch add -r<revision> <url>
    subpatch add -r <revision> <url>
    subpatch add <url> --revision=<revision>
    subpatch add <url> --revision <revision>

## Common arguments

This paragraph explains the common arguments that are used by multiple commands:

`-q,--quiet`: Suppress any output to stdout.


## subpatch list

   subpatch list

Print the path of all subprojects in the repository.


## subpatch status

    subpatch status

Show the current state of all subprojects in the superproject. It prints the
URL, integrated revision and whether the files of the subproject are changed.
E.g. if there are untracked files, unstaged changes or staged, but uncommitted
changes.

It's similar to `git status`, but not for the whole repository. Only for the
subprojects.


## subpatch add

    subpatch add <url> [<path>] [-r | --revision <revision>] [-q | --quiet]

Add the remote project specified by `url` as a subproject at the optional
`path` in the current repository.  Currently `url` can only point to a git
repository. Other subproject types are not supported yet.

The `path` is optional. If it's omitted the canonical subproject name is used.
It's mostly the last folder name in the `url`. If `path` is provided it can
include also sub directories.

If no `--revision` argument is given, subpatch uses the remote default branch
for git repositories. It's mostly the `main` branch, but the remote repository
can configured also different branches as the default `HEAD`.

`-r,--revision`: Specify the revision of the subproject that should be included
in the superproject. For git repositories it can be a branch name, a tag name
or a commit id. For performance you should give a branch name or tag name. The
git protocol allows to clone a single branch or tag efficiently. For git commit
ids subpatch needs to download the whole repository including all branches,
tags and the complete history instead of just a single revision.


## subpatch update

    subpatch update <path> [--revision | -r <revision>] [--url | -r <url>]

Update the subproject at `path`. subpatch downloads the remote repository at
`url` and unpacks the source files specified by the `revision`. All existing
and tracked files of the subproject are removed and replaced by the downloaded
files.

If no `--revision` argument is given, subpatch uses the value from the config.
Otherwise subpatch uses the new `revision` from the command line and updates
the value in the config.

If no `--url` argument is given, subpatch uses the value from the config.
Otherwise subpatch uses the new `url` from the command line and updates the
value in the config.


## subpatch configure

    subpatch configure [-q | --quiet]

Configure the current superproject to use subpatch. The command adds the
`.subpatch` config file at toplevel directory of the superproject. subpatch
uses the existens of this file as a marker that the project is using subpatch.

This command works only for git repositories as superprojects currently.
subpatch does not support other SCM tools or plain directories for now.

Normally you do not have to execute this command. `subpatch add` automatically
configures the superproject if necessary.


## subpatch apply

    subpatch configure [-q | --quiet] <patch file>

Apply the patch in the `patch file` to the current subproject. The code changes
in the patch are applied onto the source code in the directory
and the patch file is stored in the `patches` subdirectory.

You select the subproject by changing the current work directory into the
subproject.


## subpatch pop|push

    subpatch pop|push [-q | --quiet]

Pop or push the top most applied patch of the current subproject. The code
changes are reverted (for `pop`) or applied (for `push`) to the working tree of
the subproject. subpatch records the current state of applied or not applied
patches in the metadata.

You select the subproject by changing the current work directory into the
subproject.


## subpatch subtree checksum

    subpatch subtree checksum [--calc] [--check] [--write] [--get]

Calculate, check, write to the metadata or get from the metadata the checksum
of the subproject's subtree.

You select the subproject by changing the current work directory into the
subproject.


## Commands, not implemented yet

The following list is a draft for additional commands. subpatch will implement
these in that form or another.

* `rm <subproject>`: Remove subproject code and config data. The reverse of `add`.
* `mv <subproject> <new directory for subproject>`:
  Move/rename subproject to a new directory and update the config data
* `foreach <command>`: Execute a shell command for every subproject.
  All the other multi repository management tools also have such a command.
  So subpatch also needs it. See `repo foreach` and `git submodule foreach`
* `check`: Verify subproject source code, patches and config
    - check that subpatch config/subproject config is valid/consistent
    - check that patches can be reverted to obtain the original source code
    - check that a superproject diff/patch/commit-range does not break the
      invariants. (This should be used in the CI)
* `reformat`: reformat the subpatch config a consistent way. There also will be
   some sort of `--check` argument to verify the style in a CI pipeline.
* `create-patches`: from the last or multiple last commits of the subproject,
  create patches for the subproject, to fullfill the invariant.
* `root`: Show the root path of the superproject. Useful
  for something like `croot` in the AOSP. For git the command looks like
  `git rev-parse --show-toplevel`.
