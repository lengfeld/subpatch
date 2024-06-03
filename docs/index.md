# subpatch - subprojects done right!

Welcome to the website of subpatch. The tool that does subprojects right!

Currently this project is just an idea. No code yet. But the general concept is
already proven and works!

The subpatch project will provide two things:

* A command line tool called `subpatch` to manage subprojects (in a monorepo). The github
  repo is [subpatch](https://github.com/lengfeld/subpatch).
* Documentation, explanations and opinions about multi repo setups and
  management. This is this website.

If you are currently using
[git-submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) or
[repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md) and you are
frustrated, `subpatch`  will be mostly your solution! If you are interested,
email [me](mailto:stefan+subpatch@lengfeld.xyz).


## subpatch's concept

subpatch will be a subprojects management tool based on the following ideas:

* The files of subprojects are added as normal files to the superproject.
  In most cases this will be just a git repository. It's based on the idea of
  monorepos.
* The metadata of a subproject is saved in a git-config styled configuration file.
* Modifications of the subproject are possible and subpatch helps to maintain
  a linear patch stack of the modifications.
* Importing new versions of the subproject is possible and subpatch helps to
  rebase the local modifications.


## subpatch main difference

subpatch is based on the concept of
[monorepos](https://en.wikipedia.org/wiki/Monorepo).
When you use subpatch the subprojects are not git repository itself. The files
of the subprojects are added as files to the superproject. You will only have
to deal with a single git repository.

This is in contrast to other tools, e.g.

* [git-submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
* [repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md)
* [kas](https://kas.readthedocs.io/en/latest/)
* [west](https://docs.zephyrproject.org/latest/develop/west/index.html)

These tools manage multi git repository management and try to combine them into
a big superproject.  This is done on purpose. I think that only a monorepo is a
sane and viable solution.
