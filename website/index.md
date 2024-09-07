# subpatch: fearless multi-repository management - stay relaxed!

Welcome to the website of subpatch. The tool that does multi-repository
management right. Don't worry, stay relaxed!

Currently this project is just an idea. No code yet. But the general concept is
already proven and works!

The subpatch project will provide two things:

* A command line tool called `subpatch` to manage subprojects in a source control repository,
  e.g. in a git repository. The github repository is
  [subpatch](https://github.com/lengfeld/subpatch).
* Documentation, explanations and opinions about multi repo setups and
  management. This is this website.

If you are currently using
[git-submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) or
[repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md) and you are
frustrated, `subpatch`  will be mostly your solution! If you are interested,
email [me](mailto:stefan+subpatch@lengfeld.xyz).


## subpatch usecases

subpatch is interesting for you if you want to do the following tasks:

* assemble a monorepo from multiple repositories
* integrate third party dependencies into your project as source files
* maintain a local fork (=linear patchstack) of a third party dependency


## subpatch's concept

subpatch will be a subprojects management tool based on the following ideas:

* It's based on the idea of `git add` and `git read-tree`. The files of
  subprojects are added as normal files to the superproject.  In most cases
  this will be just a git repository.
* The metadata of a subproject is saved in a git-config styled configuration file.
* Modifications of the subproject are possible and subpatch helps to maintain
  a linear patch stack of the modifications.
* Importing new versions of the subproject is possible and subpatch helps to
  rebase the local modifications.


## subpatch main difference

When you use subpatch the subprojects are not git repository itself. The files
of the subprojects are added as files to the superproject. You will only have
to deal with a single git repository.

This is in contrast to other tools, e.g.

* [git-submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
* [repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md)
* [kas](https://kas.readthedocs.io/en/latest/)
* [west](https://docs.zephyrproject.org/latest/develop/west/index.html)

These tools manage multi git repository management and try to combine them into
a big superproject.

```{eval-rst}
.. Hidden TOCs

.. toctree::
    :caption: Explanation
    :maxdepth: 2
    :hidden:

    exp/intro
    exp/design
    exp/comparison

.. toctree::
    :caption: Tutorials
    :maxdepth: 2
    :hidden:

    tut/installation
    tut/basic-usage

.. toctree::
    :caption: Reference
    :maxdepth: 2
    :hidden:

    ref/glossary
    ref/releases
    imprint
```
