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

TODO: Update this DD. subpatch has `.subproject` files now that are seperate
from the subpatch config file.

**DD4**: Published as a standalone and single python script

TODO add [+] points here

**DD5**: Filenames and file system paths are python bytes objects, not strings

TODO add [+] points here

**DD6**: The subproject's history is not include in the superproject's history.

TODO E.g. git-subtree and combo-layers are doing this

TODO Including the history is against learing L4 (minimize accidentally complexity)

TODO add [+],[-] points here

**DD7**: The naming convention in config and metadata is the git config style.

In the config file `.subpatch` and metadata files `.subproject` (that are
git config files) the naming convention is *camelCase*. See
[these example from the git documentation.](https://git-scm.com/docs/git-config#_example)

* [+] Consistency, since subpatch is using the same style as git itself.

**DD8**: The git tree object SHA1 checksum is used to record the state of the
subtree(=file tree) after unpack and before patches are applied.

* [+]: Already a standard definied by git
* [+]: If superproject is git, already computed for us. No extra code needed.
* [+]: If superproject is git, already computed for us. No extra directory walk and file read needed.


*Note*: This list is not completed yet and should grow while supbatch is developed.
