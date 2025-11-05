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

**DD9**: subpatch requires python 3.11 or later

TODO

**DD10**: Using the term *subtree* instead of *worktree*

TODO explain

**D11**: License as GPLv2-only

TODO explain

**D12**: The patches of a subproject are in the folder `patches`.

* [+]: quilt is using the same folder name.
* [+]: Debian/Ubuntu source packages use the same folder name.
* [+]: The Linux kernel source code even contains a default ignore rule for the
       `patches` folder.

**D13**: The default value of `subtree.appliedIndex` in the subproject's
metadata is *all patches are applied*.

This decision follows indirectly from requirement R13. I add the requirement
and this decision to make it explicit and to note it down. At first I chose
another default value and then later noticed that it violates R13, the conflict
free merging of two changes in a subproject that are independent.

* [+]: In the clean state of the subproject, namely all tracked patches are applied,
       there is no value for `appliedIndex` in the metadata file. That fits the
       general decision principle, that the default, sane and common value is
       the default value _and_ is not recorded and shown to the user.
* [+]: Merging two histories in the superproject with changes in the subproject
       is conflict free and results in a clean state of the subproject metadata,
       when the changes (e.g. adding two independent patches in the two
       histories) are in itself conflict free. See R13.

If there would be a `appliedIndex` value in the metadata, there could be a
merge conflict for this or the value would be wrong after the merge. This is
only a very short description of the problem, but that's what I have
experienced.


*Note*: This list is not completed yet and should grow while supbatch is developed.
