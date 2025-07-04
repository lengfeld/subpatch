## TODOs and ideas

Start using pylint

Allow to lock subprojects. The CI check should error/warn, when a PR/commit
introduces changes to a subproject dir!
If a subroject is not locked, the CI would also error/warn and request the
contributer to execute a command to create a patch file!

Write test that
  $ git config -f .subpatch  subpatch."external/repo".url
works and add documentation.
This was found while reading some "git submodules" docu

Provide script to convert a
* kas
* git submodule (support recursion)
* repo
superproject to subpatch

Watch stackoverflow and respone to questions. (When the software is live.)

Text gui frontend for the layer index
(https://layers.openembedded.org/layerindex/branch/master/layers/)
to easily select and add layers to your yocto build. Replacement for kas.

Add how-to use subpatch with kas for a Yocto project

Add how-to use subpatch for Yocto project

Add how-to use subpatch for Zeyphr project

Integrated manpage into tool. Otherwise a single file install has no manpage!

Unify slogan/subtitle. fearless vs done-right

Show software/license disclaimer at more locations.

Build and test for Windows (Setup windows VM in gnome boxes?)

The command "subpatch update" (or how it's called) should be able to add the
changelog or added commits automatically to the commit message.

Add checksum of subpatch script to release page. Sign with gpg key.

Improve build process. Last time I released with uncomitted changes.

Add github action to deploy the website automatically

If subpatch is a toolkit and works nicely as a toolkit, write a "yocto layer
manager". So the same as a "package manager" but for the Yocto layers. Features
* seraching for layers
* selecting, downloading, adding layers and
* automatically resolve dependencies onto other layers
  (Core feature of package managers)

For the technical comparisons of the tools add
* the start of development

Draw/find a logo. Maybe something like '/sub/patch'.

Setup sphinx build for website.
* find differences, .e.g sitemap and 404 page.

Common problems (why you should use subpatch)
* stories/PRs/feature requests span multi repos
* checkout out a feature for review needs multipe repos
* dependend commits/atomic commits problem/two commits problem
* Anti point: devs must be trained to honor code ownership, use tools.
  (General problem of monorepos)
* disappearing of upstream recourses

Write summary for every tool that stats what feature this tool
does not implement compared to subpatch.

Write about the benefits of subpatch.

Check whether kas and west can support other superprojects than git.

Add checker that checks available of out-going links.

Add germany haftungs-stuff in the imprint.

Write about Critic/pitfalls/Bad-stuff of subpatch
* subpatch is just a generic APM. With the same problems as other APMs
  for downstream consumers, like embedded build systems.
* APM issue again: subpatch does not allow dependency resolution or sharing!
  If multiple subprojects uses itself subpatch, there is no dependency
  sharing!

Add other multi repo management tools to explanation page.

Add explanation of source/external dependency and there different types like
internal helper libraries to external projects (To the glossary)

Idea/feature request: repo and git submodules support relative subproject URLs.
These are resolved to the url of the superproject. This allows to mirror a
superproject and the subprojects without changing the URLs in the
manifest/config file. Should subpatch also support this feature?

Adding a git subprojects that has itself submodules? What should happen?
* Should the exact subproject git tree be adding inclusiv the git commit objects?
* Should the sumodules be downloaded add as plain files?
* Should it just be ignored?

Add a generic "-q/--quiet" option. Should only print errors.

Introduction typing in the code base

Add test cases to verify hat svn and hg also uses the term 'revision' and
argument `-r`.

Additional to latest, also add every version of the subpatch script on the
download folder on the website. No need to link to github.

Add/Do language and grammar checking for content on the website.

Add command (or at least check) to compare/update settings in config format
with the contents of the tree/repo.

Clearify the behavior of `subpatch add <url> <folder>/". Is the subproject then
downloaded into the folder as-is or a subfolder with the name of the subproject
created?

Document runtime dependencies. For now it's `git`.

Add site with "Things to be aware of".
- After using subpatch, you have kind of monorepo. Now you maybe have new problems:
  - git status maybe slow
  - Multiple teams working together in one repo
     - train developers to respect code maintainership/owners.
     - Shared CI by multiple teams.
       You can have multiple CI Files, e.g. on github
     - "I see pull request that I don't care".

Add "move"/mv command to move subprojects.

Add "rm" command to remove them.

Add "foreach" command

Add learning/LX: review of patches of patches is not nice.

Add learning/LX: mixing two different histories (like subtree merge) in a
single commit history or even a repository is bad.

Prior art. The AOSP uses a 'METADATA' file with a json like format to track
upstream projects.
See https://cs.android.com/android/_/android/platform/external/cblas/+/a80d2d48ce556f883aec760e28269087a957801f:METADATA

Avoid reimplementing "git rebase". But maybe neede for other vcs?!??!
-> Integrating new upstream versions with rebasing location patches is the holy
grail of this project. It cause some headaces for me.
-> Mabye first solve the MVP. subproject without changes.

subpatch goals is to help rebasing patches of a subproject to a new version.
- Write a test that uses "git apply" and works on a single commit to prototype
  the rebase procedure.

Make license for documentation, e.g. website, more explicit.

Maybe relicense the source code as "GPL-2.0-or-later". The GPLv3 has some good
extra text about handling license violations.

Write and document the patch structure format. It's the same as 'quilt' uses.
And therefore also the same as debian/deb/ubuntu uses for packages
See e.g. https://packages.debian.org/buster/liblivemedia-dev

Add tests to verify evil chars (speical ASCII, non ASCCI and utf8) chars in

Paths should be correctly escaped in the subpatch config

Add command to check validy of synxtax in config. Even useful for test, where
it's easer to just drop a ".subpatch" file instead of really "add"ing
everything.

For "add" print the commit message that is integrated

Add "rm" command

For a potential "update" command list the commits and diffstat that are integrated

Show list of added files in the "add" command. Showing the diffstat is too
huge. And it also shown when doing "git commit".

Implement implicit "<name>.git" optimization for git repos. If there is a bare
repository next the subproject use it for cloning, checkout and history
listing.

idea: If "--exclude/remove/strip" arguments are added to "supatch add", to remove
certain files and dirs from the subproject that is integrated, the argument
list can be become quite long. Maybe then the "add" argument must be splitted
into multiple commands to gradually add "--exclude/.." config options.

Implement 'foreach'. See repo and git-submodule

Implement 'rm'. The counterpart of 'add'.

Design principle: Modifiying config files by hand is ok and encouraged. Don't
add code/commands to do simple things, like adding a version parameter or ...
- Provide a check/update command to verify and/or apply updates to the working
  tree.

State of the superproject
- Not configured
- configured
   - no subprojects
   - some subprojects

Convert all paths to bytes

When the user see the error
   Error: subpatch not yet configured for superpro
on the console, the program must also write the resolution!

If there are local changes in a subproject, show in `subpatch status`,
then print also infos how to create a patch file for it!

Think about subpatch superprojects as subprojects in other repos.  Then the
subpatch config file is not at the root of the repo. Currently this is not
supported.

Implement `git rev-parse --show-toplevel` for subpatch

There is a common confusion about relative paths in the output (and on the
commandline) of subpatch or other commands: Are the paths relative to the
current working directory or to the toplevel dir of the repository.
E.g.
- the output and arguments of "git status" are relative to the cwd.
- the output of "git diff" is relative to the toplevel dir.
Think about a consistent concept and implement it.
E.g. implement an argument "-t" for toplevel of subproject or
"-T" for toplevel of superproject.

Start to use the forzen attribute for dataclasses
https://docs.python.org/3/library/dataclasses.html#frozen-instances
Make the structs/dataclasses immutable!

Naming ideas
- the superproject is "configured" or "not configured"
- the subproject is "init(ialized)" or "not initialized"
Even it's the same thing. Just a file, use diffferent names to allow the
documentation be clearer.
Another example
- It's the superproject "configuration"
- and the subproject "metadata"
Also actual synomous. So be consistent and use it for one and the other.

Add Parsing Error for subpatch config

move "history.md" to "learnings.md"

one group of users are Xcode developers. Xcode does not support git-submodules. So they
need another tool. E.g. subpatch

Document the different personas: core/maintainer vs contributor
* Pro: Only core/maintainer needs subpatch, contributor not!

Document storage requirements
* Pro: no history
* Same: checkout size is the same!
* Cons: More resources on own git server

Document/add command to construct commits from the subproject changes to push
it upstream.

Document lifecycle of patches in a down-stream fork

convention of ".gitupstream"
   https://github.com/LineageOS/android_vendor_qcom_opensource_usb/blob/lineage-22.1/.gitupstream

For command "foreach" add a group feature. Sometimes you only want to execute
commands for some repos.

Look at other tools, e.g. https://github.com/nikita-skobov/monorepo-git-tools
and the long list at https://github.com/dfetch-org/dfetch/issues/669
https://dfetch.readthedocs.io/en/latest/alternatives.html

Rewrite requirements (https://subpatch.net/exp/design/)
* Sort Rs according to improtance
* R1 should not be as important than R3 (everyone is using git anyway)

Make naming convetion fix: E.g. "metadata" should actually be "[subpatch]
config".

Add LLx/Learing: Review a patch for a patchstack is ugly.
E.g. see
https://github.com/openembedded/meta-openembedded/commit/294c0251f83671151c46fe3538e9bad27c0278bd
Better tooling is needed.

Write about the madnees of `git submodule` and recursion.

Implementing command `update/upgrade` is tricky.
* Removing the whole subproject is bad:
    * There are maybe untracked files by the user. These should not be removed.
    * For huge subprojects, e.g. AOSP, removing and readding alle files does not scale.
      subpatch should only update the files that have changed for performance.
      This alos keeps the timestamps of the files. Useful for increment builds.
* All this means that subpatch must work on diff/patches between different
  versions of the subproject.
* Should we implemented our own recursive file updated? Acutally no. git has
  already implemented this for all of it's commands!

Implementing command `update/upgrade` is tricky (II).
* There is a difference between branches and git tags/tarballs/svn revisions.
  For branches you get tracking upstream verions out of the box. Not so for tags
  or tarball links. There you must scan with a schema/regex/... for new and higher tags
  or new tarballs.
* Actually subpatch should not implemente a generic upstream-check-for-news-updates mechanism.
  subpatch should be a plumbing layer for such scripts
    * A command sequence/workflow can look like
        * `subpatch check <sub>`: verify invariant
        * `subpatch update <sub> -r <new-tag>`: try update/upgrade new version
           Checks that there are no location modifications.
           But in this example it fails. A patch does not apply.
           Everything is reverted to the original state.
        * `subpatch deapply`: roleback all patches (could also be done with quilt)
        * `subpatch check --tree-sha1-subproject`: Nearly the same as above. Verify that now working tree is the original source code.
        * `subpatch download/unpack -r <new tag> (or update --without-patches)`: Download and unpack new source code
        * `subpatch apply`: will still fail at some patches. Now the patches must be rebased/updated
        *  Rebase/update: either use quilt. Or some variant of "git rebase" or a subpatch must implemented it's on helper
           But ... `git rebase` already. It should really be used. No need to reprogram this!
        *  Now the new source is unpacked and patches are rebased
        *  `subpatch check`: verify invirant for new source code and patches
        *  `git commit`
* Or provide a hook for external scripts to check for updates.
* NOTE: These external update scripts should also point to a releasenotes/changelogs.
* subpatch should be useable for a tool like "https://github.com/dependabot"

Make DDx: Should `subpatch (de)apply` and rebase helping be based on
index-vs-working-tree or working-tree-vs-commits.
* (+) for commits: intermediate setups are backup'ed in the reflog
* (-) for commits: not atomic, commit can remain after crash/abort
NOTE: quilt stores it metadata in `.pc/applied-patches` and other files in `.pc`

If subpatch needs to implement a rebase helper, maybe just generate a rebase
sequence and let "git rebase -i" do the work!

Git already provides some ways to handle "subprojects" from the early days. It was called "bind". See
"write-tree command":
    https://git.kernel.org/pub/scm/git/git.git/commit/?id=f4c6f2d328e2f30ad63fdfca26a5e4a11cef35bf
There is also a read-tree command with prefix that we mostly do not need to use!
    https://git.kernel.org/pub/scm/git/git.git/commit/?id=f4c6f2d328e2f30ad63fdfca26a5e4a11cef35bf

Maybe the focus of subpatch is shifting: Primarly a patch stack maintaing
command and second a multip repoistory command.
E.g. "subpatch list" should print the list of patches

(maybe) goal of subpatch: define/standardize patch tracking information, e.g.:
accepted, rejected, not-applicatable
E.g. subpatch becomes the "source package manager"

Maybe make config file for subprojects more visible by not using dot prefix.
In AOSP it's also more visible, the file is called 'METADATA'
https://cs.android.com/android/platform/superproject/+/android14-qpr3-release:external/junit/

Document difference between commands for the superproject and commands for a
single subproject.

Think about the problem: subpatches uses patch files to track patches of a
subproject. upstream projects use git and pull request for submission. So the
user needs a command/way/tool to convert some of the local patches to an
upstream pull request. Mabye we need a helper command for that.

document the (funny) but important point: If the invariant is intakt, the
superproject contains the unmodified source code of the upstream project. It's
the current working tree of the subproject _and_ the patches reverted. So it
can be generated out of the information in the superproject.

Prior Art: Here some changes to the junit library are maintained by AOSP-devs
    https://cs.android.com/android/_/android/platform/external/junit/+/adac35f1ea1f9987d9843236991ad4120e704bcb
It's quite common that AOSP external sources have local changes
e.g. see https://android-review.googlesource.com/c/platform/external/conscrypt/+/3267393

Idea: the command "update" should be named "rebase". We maintain local changes
as patches, so every update is a rebase!

DDx: state of applied patches are tracked in the subpatch config.
State diagram
   None <---> No-unpacked   <---> unpacked  <--> half-patched  <---> fully-patched
                empty            raw/original      modified           modified/clean/
   none  <->    empty(*)         <->   raw     <->     modified    <->     clean
(*) A special variant of this state: empty with checksums/SHA1s and empty without!
    Bevor download and unpack there is no checksum/SHA1/tree-sha1 for the config!
    -> maybe introduce state: prepared
    But removing the source code should never be needed.
the commands are
         "init"            "download"      "apply/deapply"     "apply/deapply"
        add/rm              unpack/...          pop/push (--all)
TODO map this to the quilt commands!
TODO distinguish between lowlevel and higher level commands
if count-patches == 0, then unpacked == fully-patched == half-patched
NOtes:
* "clean" for the state is not the best work. In standard case
    "subpatch add ..."
  there are no patches. all the states fall together!
  This maybe be counterinoutive that the first state is already clean

What is the tuple of subpatch for a subproject
   (url+rev, working tree, series+patches, apply status of patches)
     + checksum of files, when in the "raw" state
     + download upstream project in cache
One issue: Not after every command, the invariant is fullfilled.
E.g. adding a patch, may invalidated the invariant.
E.g. dropping a patch is only possible if currently not applyied
But checking the invariant is possible in every state.

"subpatch add" == "cd subproject; subpatch init <url> <rev>; subpatch download; git comit"
init

Maybe new slogan: "subpatch - quilt for git"
See first messages on the mailinglist:
https://lists.nongnu.org/archive/html/quilt-dev/2003-01/msg00003.html

Think about: subpatch combines quilt-for-git (for a single project) and
sub-project management. Can these both be seperated?

Think about: A project that uses subpatch is forked. How does the downstream
handle modifications to the patches for a subproject.
-> You have a recursive problem

Think about: subprojects with a single file.
- here is a list of single file C libraries
  https://github.com/nothings/single_file_libs?tab=readme-ov-file
- There was also once a LWN article about a often plain included libraries
  (compress/crypto) with some security issues.
- Maybe also useful to integrated patches

Idea: Apart from "exclude" also add a "subtree/prefix" modifier. Get a sub
directory from a upstream project.

Write about the term "vendoring".

Prior Art: lwn comment
https://lwn.net/Articles/713350/
-> keep patches as seperate files
-> Supatch differences: patches are not applied in the build process. They are
already applied.

Thinking about plumbing commands /plugin system for subprojects
"subpatch.git" and "subpatch.svn" and "subpatch.tar"
Example script for "subpatch.tar" for "upgrade":

    subpatch check-invariant
    subpatch pop --all
    # a this point the invariant is broken
    new_version=$(subpatch get version | sed bal)
    wget $(subpatch get url)  $new_version
    subpatch plumbing-unpack $tarball
      - only updates existing files without "rm -rf*" to avoid deleting work in progress files
      - alternative, using patch file to update sources
      - alternative, using commit range to update sources
    subpatch set rev $new_version
    subpatch set url $url
    subpatch check-downloaded-raw
       - only works if cache contains original tarball or commit id
    # a this point the invariant is still (maybe) broken, maybe the patches do not apply
    subpatch push --all  # in case of no errors
    subpatch check-invariant
    # a this point the invariant holds again.
    git commit -m "add new tarball"

Command sequence for remote/subproject is a script and uses subpatch as plumbing commands

   subpatch init
   wget <tar>
   tar xf ...tar.gz
   supbatch update-raw-checksum
   git add .
   git commit -m "adds subproject"
   # and then
   subpatch init patch
   subpatch patch export-from-superproject
   git add patches
   git commit -m "add patches"
   # TODO Nothing is remebering the url and rev of the subproject here!

   # update subproject
   # TODO does not get or update config values
   subpatch check-invariant
   subpatch pop --all
   wget <tar>
   subpatch list-files-of-subproject-in-raw-and-compare-with-tar-and-update-local-files
   subpatch push --all # and hope there are no conflicts
   subpatch check-invariant # holds again


what are the commands for the plugin system
   - download full version to cache
   - download delta version to cache
   - set url/rev/version of new upstream source

".subproject" config
    [subproject]
        name = xxx # maybe
        raw-checksum = 123123
    [remote]
        type = git
        url = https://xx
        rev = branch
        commit = 1231234123
        tag = 12312321
    [remote]
        type = tarball
        url = https://
        sha1sum = 123123
    [patches]
        dir = patches/
        patch = <filename>
    # What is the default state? With "patches" section or without?

states-dimensions of a single subproject:
    - nothing/empty
    - configured
      - source code not populated
      - source code populated
        - no patches
        - some patches exists:
           - no applied  (raw)
           - some applied (modified)
           - all applied (clean)
    - NOTE: theo. there can be also a state with no-popluated, but patches

   and for the cache (state-remote is init'ed):
    - no remote configured
    - remote configured
       - cache contains full tree
       - cache contains next tree
       - cache contains diff for next tree
       NOTE: This does only make partial sense for git repos.
       - It always contains the whole trees
   tuple:
     (config, working tree, series+patches, apply status of patches)
      + download cache


For tarball diff update tesing, use the kernel incremental patches. See
    https://kernel.org/

Topic: Single file subprojects
- What should the config syntax be?
   O1: Extra config file with suffix ".subproject"
    bad: not a hidden file as the normal ".subproject" file
    good: content would look different for normal and single-file subprojects
   O2: Subsections in directory specific config file ".subproject"
    good/bad: Must work with subsections. Looks ugly if more sections like
      "remote" and "patches" are used.
- How to specific the single file subproject on the commandline if there are multiple
  single-file subprojects in the same directory
   -> Open question. Mostly per argument

What does a ".subproject" config look like for a single file (e.g. a patch file)
    [subproject "001-fix-some-thing.patch"]
        url = https://github.com/xxx/repoA
        raw-checksum = 123123
    [remote "001-fix-some-thing.patch"]
        type = git
        rev = main
        commit = 1231234123
        file = patches/001-fix-some-thing.patch"
    How did the command look like:
    $ subpatch add https://github.com/xx/repoA --file patches/001-fix-some-thing.patch --rev main
    $ git commit -m "adding file"
    What are the sub commands:
    $ cd patches
    $ subpatch init --file 001-fix-some-thing.patch
    $ subpatch remote init git
    $ subpatch remote set-url http://github.com/xx/repoA
    $ subpatch remote set-rev main
    $ subpatch remote set-file patches/001-fix-some-thing.patch
    $ subpatch download
    $ subpatch unpack
    $ git commit -m "adding file"
NOTE: For single file dependencies there can be multiple "subproject" sections
in the ".subproject" config!

what are commands for patches?
- drop # a single patch
- add # a single patch ontop or inbetween, existing or new
- modify # a single patch (called refresh in quilt)
- add # a whole series of patches
- push/pop   # apply and deapply patches

"subpatch create-patch":
- either creates a patch from an existing commit or
- creates a patch and commit from existing stagged files in the index

The ".subproject"'s config file section "remote" is nearly the same as a "git
remote". Why is it ok to reimplement this? Why is it not possible to reuse git?
- Reason 1: …, because git only has 'git' remotes. subpatch should be more generic.
   But bad reason, beacuse in most cases subpatch will also use git remotes
   Or even recommend to convert non-git remotes to git remotes for diff updates
- Reason 2: …, it's not the problem. subpatch sill uses the "git" command to
  handle git based subprojects. It does not rework/recode 'remote' handling
- Observation: ".submodules" have a same concept. A config file that is tracked
  that can be used to "init" the remotes in the superproject.

Define orthogonality or commuative property of patches? (=Patches that do not
interfere)

Implementing diff-detla updates for non-git subprojects is very specific to a
subproject. Only a view tarball subprojects release diffs/patches. E.g. the
Linux kernel does, but I don't know other projects. So it's very project
specific and cannot be implemented in subpatch.
-> This must be handcoded for every project itself.
   -> This would require more source project management, like build root or yocto

Define/think about subproject update automation.
- It requires a way to list all projects released versions
- sorting between the versions
- querying if a update is available.
All this is project specific.
(Or solved by an APM, like pip or npm, because they have introduced conventions
for that!)

Look at "umpf": https://pengutronix.de/de/blog/2023-08-29.html

subproject config documentation:
  [local]
     checksum = tree object of git of the original local source code
     ignore = paths/files that are ignored, but tracked by the superproject, e.g. ".subproject" and "patches/"
  [remote]
     url = <git url>   # this is a standard for all subproject types
     revision = <name that was included>   # this is a standard for all subproject types
     commit-id = # if used
     tag-id = # if used
     checksum-shaX = # if it was a tarvalld
     subtree = # if a subtree is selected   # also standard
     exclude = # if some stuff is excluded. mabye support globbing  # also standard
  [patches]
     patch = name/path of the current top patch!
        # a single patch can be adding and the "subpatch push" command executed
     series = # path to series file, maybe can be multiple files
     patches = # dir to patches file, can be multiple dirs!

subproject tuple:
   (working dir, local-config in config, remote config in subproject, cache+cache info, patches+applied state in config)
   (W, C_local, C_remote, D+info, P, P_config)
subproject state:
   - nothing
   - inited
      1) a remote does not exists
         b remote exists
      2) a nothing in cache
         b upstream/tarball downloaded
      3) a no patches
         b some patches
           - all patches applied (<- clean)
           - some patches applied
           - no patches applied

subproject command
    subpatch (patch) pop,push
    subpatch (local) calc-checksum-and-write, init, deinit
       # checksum calc works only, when no patches are applied!
    subpatch (remote) download # with new version/url
    subpatch (remote) unpack
       # unpack files in download-cache to working tree
       #  - only works if no patches are applied
       #    or command must update the checksum
    subpatch remote check
       # compare local working tree against download stuff
       # -  only works if all patches are deapplied
    subpatch local check
       # compare hash in config against working tree
       # -  only works if all patches are deapplied
       # Note is the same as "patch check", but without auto-deappliy -.-
    subpatch patch check
       # check that if all patches are deapplied that the checksum matches
    subpatch update
       - subpatch pop --all
       - subpatch check
       - subpatch download [<url>] [revision]
         # Does this already update the config?
       - subpatch unpack
         # unpack from cache in to working directory
         # _and_ update the remote-config
         # Invariant is maybe broken here, because patches my not applied
         # NOTE: The clean state is not reached!
       - subpatch push --all
    subpatch add
       - subpatch init
       - subpatch download url (rev)
       - subpatch unpack

Invariant is

    Working tree --deapply patches--> Woring-tree! == Original integrated source
    pre-condition: state is "fully applied"

Rethink `GPL-2.0-only` license. GPL-2.0-and-later should also work! Add DD for that

Mabye using "fetch" instead of "download", because the term fetch is already used by "git"

Use term "init" for the superproject, because "git submodule" also uses "init".
So it's the "superproject is initialized".
Answer: No, "init" is for the submodules aka subprojects

Write about common issues and critic:
* subpatch promotes vendoring
* subpatch creates monorepos with the monorepos problems
* subpatch is also just a wrapper around git
* subpatch increases the repo size and storage size!

Subpatch will/should allow a new class of tools: "CPM" - "(Source) code package managers"
-> a tool like kconfig to enable and download yocto layers.
- subpatch as a plumbing command
-> Big learning: software distritbution does not need to be the original source code.

Subpatch can also allow "PSM" tools: "patch stack managers". Integrate and download
different patchstack and put them together
-> the hosting side can track if patch stacks are compabilte or are conflicting!

Use mypy and pyright for type checking. And add more type signatures.

Look at Yes, indeed, but that is if you already have selected a dependency, next to that some kind of index would also be great

Look at https://libraries.io/login to get updates for dependencies

libs for fancy TUI/GUI:
https://github.com/Textualize/rich
https://github.com/Textualize/textual

Split "supatch.py" in multiple files, test in isolation and merge for publishing
-> better source code structure, but still just one file for distribution

Check for spelling mistakes. E.g. "TOOD"

State of subprojects
 - subtree contains files: populated
   - metadata contains checksum of unpatched, but unpacked files
   - state of applied patches, e.g. none or all
   - infos about upstream, url, rev, sha1, checksums
      NOTE: this is more part of upstream
 - cache
    - type of download: git, svn repo or tarball
    - contains metadata: url, rev, commit/tag id (in git called FETCH_HEAD)
    - more metdata: supatch is owning the cache, or it's a seperate cache: cannot clear!
    - this repo can also be used to rebase patches, and create a pushable branch from a patchlist
 - patches
    - directory infos
 - unpack metadata (not really a dimension)
    - contains "subtree" and "exclude" directies
 - upstream:
    - contains url of upstream project for git clone
      can be different types, git, svn, tarvall
commands for subproject
 - init
 - download
 - unpack
 - pop, push
 - commit-to-patch
 - ls-worktree-files (needed for 'update' to remove only our own tracked files)
 - 'git rebase' like tool to modify patches
But: don't reinvet the wheel?

different types of commands
- tier 0: No inputs from subprojects, only superproject
    - list
    - foreach
    - configure
- tier 1: only one one dimension
    - cache drop
    - cache init --type <type>
    - cache fetch <url> <rev>
    - worktree ls # list files
      Is worktree the best name?
    - worktree drop
    - patch drop  # makes not so much sense, because it does not deapplies the patches
- tier 2: on two dimensions
   - download (uses cache and worktree)
   - unpack (uses cache and worktree)
   - pop, push (uses patches and worktree)
   - apply <patch file> (uses patches and worktree)
   - drop <patch> (uses worktree and patches, deapplies, drops and reapplies)
   - check-unpack (compare worktree with cache content), no patches
   - check-patches: (deapply patches, check worktree checksum), no cache
   - add: uses cache, worktree (only worktree and cache, not patches)
   - patches-to-branch: (uses patches and cache, not worktree)
- tier 3: on four/all dimensions
  - update: uses patches, cache, worktree
  - status: 

Convert all paths to bytes

@ -399,8 +446,36 @@ Naming ideas
Even it's the same thing. Just a file, use diffferent names to allow the
documentation be clearer.
Another example
- It's the superproject "configuration"
- It's the superproject or subpatch "configuration"
- and the subproject "metadata"
Also actual synomous. So be consistent and use it for one and the other.

Maybe use the term "upstream" instead for "remote" to more distinguish to git.
-> make this to a DD
      git      | subpatch
      ---------|---------
      remote   | upstream
      checkout | subtree  (worktree is already used for a git feature)
      ".git"   | cache
      "branch" | patches

Add Parsing Error for subpatch config

move "history.md" to "learnings.md"

one group of users are Xcode developers. Xcode does not support git-submodules. So they
need another tool. E.g. subpatch

Document the different personas: core/maintainer vs contributor
* Pro: Only core/maintainer needs subpatch, contributor not!

Document storage requirements
* Pro: no history
* Same: checkout size is the same!
* Cons: More resources on own git server

Document/add command to construct commits from the subproject changes to push
it upstream.

Document lifecycle of patches in a down-stream fork

convention of ".gitupstream" 
https://github.com/LineageOS/android_vendor_qcom_opensource_usb/blob/lineage-22.1/.gitupstream

For command "foreach" add a group feature. Sometimes you only want to execute
commands for some repos.

Look at other tools, e.g. https://github.com/nikita-skobov/monorepo-git-tools
and the long list at https://github.com/dfetch-org/dfetch/issues/669
https://dfetch.readthedocs.io/en/latest/alternatives.html

Settle on convention for: byte object to str for stdout console! The code has a
lot of ".decode()" call-sites.

There is a "unpoplated" state
- in that case the worktree is empty. But there is enough info "url+checksum" and patches
  to reconstructe everything else

Look at feature
https://blog.gitbutler.com/going-down-the-rabbit-hole-of-gits-new-bundle-uri/

state of a patch
 - active: means it should be applied to the subproject
 - applied: wehther it's applied to the worktree
 -  non-active and applied: does not exists

There are also patch stacks
 - but there is still a global/linear order of all patches

Implement: https://www.bestpractices.dev/en/criteria/0 
e.g. "security.txt"


Filesystem tree to dimensions
   filename     dimension
   .subpatch    config
   .subproject  (contains sections) /metadata
                  [patches]
                  [upstream]
                  [worktree/subtree)
   patches/*    patches
   <subproject-name>.git   cache
   <subproject dir> worktree/subtree


E.g. repo failing in real live. See 
   https://groups.google.com/g/android-building/c/c4_W34xH55I
   > The https://android.googlesource.com/platform/manifest/+/refs/tags/android-16.0.0_r1/default.xml includes https://android.googlesource.com/platform/external/v4l-utils but there's no android-16.0.0_r1 tag for that project yet so the repo sync is failing. All of the other projects have the tag. 
   https://groups.google.com/g/android-building/c/KnDgeI6c6x4
   > android 16.0.0_r1 & r2 manifests reference platform/external/v4l-utils, but the v4l-utils repo is missing the corresponding tags.
But it was quickly fixed
-> Add this to the documentation

Also allow to track binary artifacts with subpatch
Supatch. the remote asset tracker!


Repo push failure again
    https://issuetracker.google.com/issues/427013231
    "Git tag `android-15.0.0_r0.2` was overwritten wrongly with a Android 16 release on some/a lot of repos on https://android.googlesource.com/"
