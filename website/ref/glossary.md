# Glossary

This page contains explanations of the terms in the context subpatch. The terms
are _not_ sorted alphabetically. They are sorted according to relevance. More
important terms are at the top, less important terms are at the bottom.


## multi repository management/setup/problem

The *multi repository problem* is when your project consists of multiple
repositories and there are interdependencies between these repositories. E.g.
when you must checkout multiple repos, because your build spans across multiple

On this website the problem is sometimes called *multi repository setup*. The
process of handling such a project is called *multi repository management*.


## superproject

The *superproject* is the parent project in a multi repository setup. It's often
a git repository itself, e.g. for `git submodule`. When using subpatch the
superproject has the configuration file `.subpatch` at its top level directory.


## subproject(s)

The *subproject* or *subprojects* are the external projects, often called (third
party) dependencies, that are added to the superproject.

*Note*: The terms *super-* and *sub-*projects are always relative to a specific
project setup. It might be the case that the superproject of a project (e.g. a
C library with third party dependencies) is the subproject of another project
(e.g. a C++ application, using the library).


## Naming in different contexts

The terms superproject/subproject and project/dependency are specific to a
given context, but can be used interchangeably. Here is an overview:

| Context            | Name for super…  | Name for sub…         |
| ------------------ | ---------------- | --------------------- |
| package manager    | project/package  | (source) dependencies |
| multi repo problem | superproject     | subprojects           |
| multi repo problem | super repository | sub repositories      |
| multi repo problem | superrepo        | subrepos              |


## version control system (vcs)

A *version control system* is a tool to track changes to a set of files and provides
auxiliary functional. Sometimes these are also called *source code management* tools.

Popular version control systems are

* [git](https://git-scm.com/)
* [subversion (svn)](https://subversion.apache.org/)
* [mercurial](https://www.mercurial-scm.org/)
* [Concurrent Versions System (cvs)](http://savannah.nongnu.org/projects/cvs)

The older name for vcs is *rcs* (*revision control system*). And yet another
(current) name is *scm* (*source control management*). Then name is used
on the [git website](https://git-scm.com/).


## application-level package manager (APM)

The term *application-level pakcage managers* (APM) is used to described
package managers provided in the ecosystem of the programming language. Examples:

* [yarn](https://yarnpkg.com/) for Javascript
* [cargo](https://crates.io/) for rust
* [pip](https://pip.pypa.io/en/stable/) for python
* [conan](https://conan.io/) for C++

See also the Wikipedia entry
[Application-level package managers](https://en.wikipedia.org/wiki/List_of_software_package_management_systems#Application-level_package_managers).
These APMs are in contrast to package managers of Linux distributions, like rpm and
dpkg, and embedded build systems, like buildroot and Yocto.
