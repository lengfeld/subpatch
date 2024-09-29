# Command line arguments

The subpatch command line tool uses the common argument structure with multiple
arguments and one command. It is the same as other popular tools like `git` or
`docker`. Examples:

    subpatch status
    subpatch add <url> -r <revision>

Here `status` and `add` are commands and `-r <revision` is an optional
argument. 

subpatch uses the [argparse module](https://docs.python.org/3/library/argparse.html) of python.
So the following commands are equivalent:

    subpatch add -r=<revision> <url>
    subpatch add -r<revision> <url>
    subpatch add -r <revision> <url>
    subpatch add <url> --revision=<revision>
    subpatch add <url> --revision <revision>



## subpatch status

    subpatch status

Show the current state of all subprojects in the superproject. Much like `git
status`.


## subpatch add

    subpatch add <url> [<path>] [--revision | -r <revision>]

Add the subproject at `url` at the optional `path` in the current repository.
Currently `url` can only point to a git repository. Other subproject types
are not yet supported.

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
