# subpatch: internal README file

## subpatch's wobsite

This is the source of the website [subpatch.net](https://subpatch.net).
It's generate with [mkdocs](https://www.mkdocs.org/) and uses the
[material theme](https://squidfunk.github.io/mkdocs-material/).

How to test locally:

    $ mkdocs serve

How to deploy:

    $ mkdocs gh-deploy


### Background

The structure of the website/documentation is based on
[The Grand Unified Theory of Documentation](https://docs.divio.com/documentation-system/).
It structures documentation into four categories:

* explanations
* tutorials
* how-to guides
* reference


### Conventions

The term 'subpatch' is always spelled lowercase. Even at the start of sentence.


## How to develop?

Useful makefile targets

    $ make tests
    $ make lint

The project is adopting `ruff` as a python linter and checker. Currently only a
very limited set of rules is enabled, but this should change in the future:

    $ ruff check subpatch.py
    $ ruff check subpatch.py --fix  # ruff can also fix directly

Note: Use `make lint` to also check the python code in the folder `tests/`.

The codebase also starts to use type annotations. Check these with

    $ mypy subpatch.py

The codebase uses unit and integration tests extensively. To execute a single
tests

    $ python3 tests/test_prog.py TestNoCommands.test_version
    $ tests/test_prog.py TestNoCommands.test_version

Tips: If a test fails, e.g., because of a difference in the console output, you can use

    $ DEBUG=1 tests/test_prog.py TestNoCommands.test_version

to print stdout and stderr of the subpatch invocation to the console for
further inspection.


## How to release

*Note*: This section has still some rough edges.

First all tests should be green:

    $ make tests

Second the necessary tools must be installed:

    $ sudo apt-get install python3-build twine

Increase version number, create commit and tag. Replace `X` with the current
version number.

    $ vim subpatch
    $ git add -p subpatch
    $ git commit -m "Release version v0.1aX"
    $ git show  # check
    $ git tag -m "subpatch version v0.1aX" v0.1aX
    $ git show v0.1aX  # check
    $ git describe     # check

Build release

    $ make dist

Test installation locally

    $ pipx install dist/subpatch-*.whl
    $ subpatch --version
    # make some tests "status" and "add" command

    # Remove it for later install with testpypi
    $ pipx uninstall subpatch

Publish release on testpypi website

    # TODO ensure API token in ~/.pypirc
    $ twine upload --repository testpypi dist/*
    # Check website
    #   https://test.pypi.org/project/subpatch/

Make test install from test pypi

    $ pipx install -i https://test.pypi.org/simple/ subpatch

    # make some tests
    $ subpatch --version

    $ pipx uninstall subpatch

Publish release commit and tag

    $ git push origin main --follow-tags --dry-run
    To github.com:lengfeld/subpatch.git
       479f2d4..9ed50ba  main -> main
     * [new tag]         v0.1a2 -> v0.1a2
    $ git push origin main --follow-tags

    # Check tag website on github
    https://github.com/lengfeld/subpatch/tags

Make release to real pypi

    $ twine upload dist/*
    # visit website
    #    https://pypi.org/project/subpatch/

    # Install with pipx
    $ pipx install subpatch

    # Check with
    $ subpatch --version

Publish release on website:

    $ cp subpatch website/downloads/latest/subpatch
    $ mkdir website/downloads/v0.1aX
    $ cp subpatch website/downloads/v0.1aX/subpatch
    $ vim website/ref/releases.md   # write release notes and changelog
    $ git add website/downloads/ website/ref/releases.md
    $ git diff --cached
    $ git commit
    $ git commit -m "add v0.1aX release to website"
    $ mkdocs serve
    $ git push origin main --dry-run
    $ git push origin main
    $ mkdocs gh-deploy

Make release on github:

* Goto https://github.com/lengfeld/subpatch/releases
* Create release
* Title `subpatch version v0.1aX`
* Add text:

      See the [release notes webpage](https://subpatch.net/ref/releases/#v01aX)

* Mark as pre-release

Should look like the other releases.


## Code style

Not much conventions yet. For naming in python stick to the
[Google Python Style Guide - Naming](https://google.github.io/styleguide/pyguide.html#316-naming).


## TODOs and ideas

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


Implement commaands:
- 'foreach'. See repo and git-submodule
- 'rm'. The counterpart of 'add'.
- 'move'/mv command to move subprojects.
- `git rev-parse --show-toplevel` for subpatch

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

Add support and tests for a single subproject at the toplevel directory of the
superproject.

Add code and test for "subpatch update <path> --use-head-again".
-> the revision key in the metadata should be removed.

New feature of git. Donwload a single revision in "git clone". see

    https://github.com/git/git/compare/0cc13007e5d50b096c95047680ace56749c18789...337855629f59a3f435dabef900e22202ce8e00e1
    https://github.blog/open-source/git/highlights-from-git-2-49/

use this!

Thing about encoding the the program
- Encoding for shell arguments and console output (is/must always be the same)
- Encoding of the filesystem (non-repo files)
- encoding of the files in the repository
   Maybe the repo contains multiple files with different encodings
(maybe (or even a must) boths must be the same

Command/instructions how to recreate the patches/the patchstack in the patches/
folder, e.g. to clean them up.

Add command pretty print the current patch stack
- higlight the current applied patch and active/non-actice patches

Renumbering patches files, e.g. on drop. Make a DD
- either rename all, causes a big diff
- or just on user wish
- or use "series" file!

Extend ruff:
- enable more rules

"subpatch status" should print the current applied patch, if not all patches are applied!

pop/push must make a success messages with patch name
- must show a diff statu
- must show the command to continue!

Put "objectId" into [worktree] and not [upstream]!

Make naming convention "upstream" in the code. move all git repos in the tests
from "subproject" to "upstream" as the remote directory! The path in the
superproject should still be "subproject".
