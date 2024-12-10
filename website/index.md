# subpatch: fearless multi-repository management - stay relaxed!

Welcome to the website of subpatch. The tool that does multi repository
management right. Don't worry, stay relaxed!

If you are currently using
[git-submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) or
[repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md) and you are
frustrated, subpatch  will be mostly your solution! If you are interested,
email [me](mailto:stefan+subpatch@lengfeld.xyz).


## Quick start

If you want to try out the subpatch tool really quickly, follow the
instructions:

    # First go into the toplevel directory of your project that is using git, ...
    $ git status

    # then download the subpatch python script, ...
    $ wget https://subpatch.net/downloads/latest/subpatch
    $ chmod +x ./subpatch

    # and finally add a subproject to your (super)project!
    $ ./subpatch add https://github.com/google/googletest external/googletest -r v1.15.2
    $ git commit -m "adding googletest"

If you are interested in finding out more, please see the text below and the
menu of this website on the left side. It contains explanations, tutorials and
references about subpatch.


## Usecases

subpatch is interesting for you if you want to do the following tasks:

* assemble a monorepo from multiple repositories
* integrate third party dependencies into your project as source files
* maintain a local fork (with a linear patchstack) of an upstream project


## Concept and design

subpatch is a multi-repository management tool based on the following ideas:

* It's based on `git add`. The files of subprojects are added as normal files
  to the superproject.
* Subprojects are in most cases just other git repositories.
* The metadata of a subproject is saved in a git-config styled configuration file.
* Modifications of the subproject are possible and subpatch helps to maintain
  a linear patch stack of the modifications.
* Importing new versions of the subproject is possible and subpatch helps to
  rebase the local modifications.


## Main differences to other tools

When you use subpatch the subprojects are not git repository itself. The files
of the subprojects are added as files to the superproject. You will only have
to deal with a single git repository.

This is in contrast to other tools, e.g.

* [git-submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
* [repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md)
* [kas](https://kas.readthedocs.io/en/latest/)
* [west](https://docs.zephyrproject.org/latest/develop/west/index.html)

These tools manage multiple git repositories at once. Based on a manifest file
multiple git repositories are cloned from different upstream sources into your
local checkout.

The page [Comparison to other tools](exp/comparison.md)
describes the differences in more detail.


## Website, documentation, license and code

On the website you find more information, e.g.
explanations, tutorials and references. New subpatch releases are announced on
the [release notes](ref/releases.md) pages, including the
release notes and changelog.

The source code of the program and the website can be found in the
git repository [github.com/lengfeld/subpatch](https://github.com/lengfeld/subpatch).
I have licensed the source code of subpatch as
[GPL-2.0-only](https://spdx.org/licenses/GPL-2.0-only.html),
It's the same license that is also used for the Linux kernel or git itself.


## Support

For now there is no dedicated support forum/chat/… . You can either
email [me](mailto:stefan+subpatch@lengfeld.xyz) or open on issue on
[github](https://github.com/lengfeld/subpatch/issues).
