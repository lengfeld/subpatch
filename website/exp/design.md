## Design decisions

While developing subpatch, I took the following design decisions. The
[requirement list](requirements.md) still gives a lot of freedom for the
implementation. Therefore this page documents and explains the chosen decisions
here.

**DD1**: written in python3 (but open for a port to another language later if successful)

* [+] faster iteration speed
* [+] Easier deployment/install for users of subpatch. python runs everywhere.
* [+] Programming language that I know really good and written a lot of code
  already.

**DD2**: config file format is `git-config`

* [+] the same config format that the main scm tool for subpatch (=git) uses.
* [+] Most developers are already familiar with the config format, e.g. because
  they are modyfing `~/.git config`.

**DD3**: The config is a single file and placed at the root of the repository

* [+] The project's root directory can be found even without scm. E.g. after
  the source code was exported with `git archive`.
* [+] A single file avoids a search in all sub directories. Can be expensive
  for big projects.

**DD4**: Published as a standalone and single python script

TODO add [+] points here

*Note*: This list is not completed yet and should grow while supbatch is developed.
