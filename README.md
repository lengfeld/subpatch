# subpatch: fearless multi-repository management - stay relaxed!

subpatch is currently only an idea, but based on proven concepts.
See the website [subpatch.net](https://subpatch.net) for more details.

If you are interested create a github issue or email
[me](mailto:stefan+subpatch@lengfeld.xyz).

This project is licensed under the terms of the GPLv2 or later license.


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
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

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

Update the README from the website:

    $ ./update-website.sh
    $ git diff
    $ git commit -a # if necessary

Increase version number, create commit and tag

    $ vim subpatch
    $ git add -p subpatch
    $ git commit -m "Release version v0.1a2"
    $ git show  # check
    $ git tag -m "subpatch version v0.1a2" v0.1a2
    $ git show v0.1a2  # checks
    $ git describe     # check

Build release

    $ make dist

Test installation locally

    $ pipx install dist/subpatch-0.1a2-py3-none-any.whl
    $ subpatch --version
    # make some tests "status" and "add" command
    $ pipx uninstall subpatch

Publish release on test pypi website

    $ twine upload --repository testpypi dist/*
    # Check website
    #   https://test.pypi.org/project/subpatch/0.1a2/
    # and
    #   https://test.pypi.org/project/subpatch/

Make test install from test pypi

    $ pipx install -i https://test.pypi.org/simple/ subpatch
    # make some tests
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

Make release on github

    Goto https://github.com/lengfeld/subpatch/releases
    - Create Release
    - Add release notes
    - Add subpatch script as a binary artifact
    - Marke as pre-release
    Looks like
       https://github.com/lengfeld/subpatch/releases/tag/v0.1a2


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

Strip ".git" from URL after cloning. Should not happen

   $ subpatch  add https://github.com/google/googletest.git
   Adding subproject 'googletest.git' was successful.

Unify slogan/subtitle. fearless vs done-right

Show software/license disclaimer at more locations.

Build and test for Windows (Setup windows VM in gnome boxes?)

The command "subpatch update" (or how it's called) should be able to add the
changelog or added commits automatically to the commit message.

Sync github release page and website release page.

Add checksum of subpatch script to release page. Maybe sign with gpg key.

Improve build process. Last time I released with uncomitted changes.

Use version/tag in example docs/tut/basic-usage.md and remove the explanation.

Add github action to deploy the website automatically

If subpatch is a toolkit and works nicely as a toolkit, write a "yocto layer
manager". So the same as a "package manager" but for the Yocto layers. Features
* seraching for layers
* selecting, downloading, adding layers and
* automatically resolve dependencies onto other layers
  (Core feature of package managers)

For the technical comparisons of the tools add
* the programming language
* the start of development

Draw/find a logo. Maybe something like '/sub/patch'.

Setup sphinx build for website.
* find differnces, .e.g sitemap and 404 page.

Common problems (why you should use subptach)
* stories/PRs/feature requests span multi repos
* checkout out a feature for review needs multipe repos
* dependend commits/atomic commits problem/two commits problem
* Anti point: devs must be trained to honor code ownership, use tools.
  (General problem of monorepos)
* disappearing of upstream recoures

Write summary for every tool that stats what feature this tool
does not implement compared to subpatch.

Write about the benefits of supatch.

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

Add a very short and fast getting started guide to the frontpage. More detailed
install instructions are provided as tutorials. But a reader should start very
very quickly.
