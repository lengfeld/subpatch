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

How to execute a single tests

    $ python3 tests/test_prog.py TestNoCommands.testVersion
    $ tests/test_prog.py TestNoCommands.testVersion


## License - full disclaimer

    Copyright (C) 2024 Stefan Lengfeld

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; as version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


## How to release

*NOTE:* This section is still work-in-progress.

First all tests should be green:

    $ make tests

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

    $ twine upload --repository testpypi dist/*
    # Check website
    #   https://test.pypi.org/project/subpatch/0.1a2/
    # and
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

Publish release on website

    $ cp subpatch website/downloads/latest/subpatch
    $ vim website/ref/releases.md
    # TODO continue here

Make release on github

    Goto https://github.com/lengfeld/subpatch/releases
    - Create release
    - Add link to release notes on webste
    - Add subpatch script as a binary artifact
      TODO remove that
    - Mark as pre-release
    Looks like
       https://github.com/lengfeld/subpatch/releases/tag/v0.1a2


## Code style

Not much conventions yet. For naming in python stick to the
[Google Python Style Guide - Naming](https://google.github.io/styleguide/pyguide.html#316-naming).


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
* find differnces, .e.g sitemap and 404 page.

Common problems (why you should use subpatch)
* stories/PRs/feature requests span multi repos
* checkout out a feature for review needs multipe repos
* dependend commits/atomic commits problem/two commits problem
* Anti point: devs must be trained to honor code ownership, use tools.
  (General problem of monorepos)
* disappearing of upstream recoures

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
"APM" stands (mostly) for application (specific) package manager
See https://lpc.events/event/18/contributions/1747/attachments/1551/3232/LPC%202024%20-%20APMs.pdf

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

Add command (or at least check) to compare/update seetings in config format
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
