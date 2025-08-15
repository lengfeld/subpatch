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


## version control system (VCS)

A *version control system* is a tool to track changes to a set of files and
provides auxiliary functional.

An very old implementation of a version control system is the
[*revision control system* (RCS)](https://en.wikipedia.org/wiki/Revision_Control_System).
Current popular version control systems are

* [git](https://git-scm.com/)
* [subversion (svn)](https://subversion.apache.org/)
* [mercurial (hg)](https://www.mercurial-scm.org/)
* [Concurrent Versions System (cvs)](http://savannah.nongnu.org/projects/cvs)

Other names for version control system are

* *source control management* (SCM) (used on the [git website](https://git-scm.com/))
* *source code control system* (SCCS)
* *source code management*

A non exhaustive list of non so popular version control systems is

* [darcs](https://darcs.net/)
* [Jujutsu](https://jj-vcs.github.io/jj/latest/)
* [GNU bazaar](https://en.wikipedia.org/wiki/GNU_Bazaar) [discontinued]
* [Pijul](https://pijul.org/)
* [perforce](https://www.perforce.com/products/helix-core)
* [fossil](https://www.fossil-scm.org/home/doc/trunk/www/index.wiki)


## application-level package manager (APM)

The term *application-level package managers* (APM) describes package managers
that are integrated into the ecosystem of a programming language. Examples:

* [yarn](https://yarnpkg.com/) for Javascript
* [cargo](https://crates.io/) for rust
* [pip](https://pip.pypa.io/en/stable/) for python
* [conan](https://conan.io/) for C++

See also the Wikipedia entry
[Application-level package managers](https://en.wikipedia.org/wiki/List_of_software_package_management_systems#Application-level_package_managers).
These APMs are in contrast to package managers of Linux distributions, like rpm and
dpkg, and embedded build systems, like buildroot and Yocto.


# patch and patch file

A *patch* or *patch file* is a textual representation of a source code
modification. It consists of a patch message describing the change and a diff
of the changed code lines.

When using git, you can create a patch file with the command `git format-patch`
from a commit object. For example:

    $ git format-patch e311aaded0a49dced437f2f4be0d2fce4c698132 -1
    0001-website-fix-warning-in-mkdocs-serve.patch
    $ cat 0001-website-fix-warning-in-mkdocs-serve.patch
    From e311aaded0a49dced437f2f4be0d2fce4c698132 Mon Sep 17 00:00:00 2001
    From: Stefan Lengfeld <stefan@lengfeld.xyz>
    Date: Fri, 7 Feb 2025 23:10:18 +0100
    Subject: [PATCH] website: fix warning in 'mkdocs serve'

    ---
     website/ref/fosdem25.md | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)

    diff --git a/website/ref/fosdem25.md b/website/ref/fosdem25.md
    index 5dae49e..dca35b8 100644
    --- a/website/ref/fosdem25.md
    +++ b/website/ref/fosdem25.md
    @@ -26,6 +26,6 @@ Thanks!
     Content:

     1. Present call to action
    -2. Present [homepage of subpatch](/)
    +2. Present [homepage of subpatch](../index.md)
     3. (Maybe) Do a showcase
     4. Repeat call to action :-)
    --
    2.43.0

Patches are a very old concept of distributed software development.
Developers used them even before SCM tools like cvs, svn, and git existed.
For some software projects, e.g. the [Linux kernel](https://kernel.org), patch files
sent to a *mailing list* are an integral part of the development model even today.


# source code reproducabilty

I use the term *souce code reproducabilty* to describe to process and tools to
be able to restore and checkout the full source code of our software project
for all previous releases.

E.g. if you use embedded build systems like *buildroot* and *Yocto*, your local
repositories do not contain the source code of the software packages. buildroot
and Yocto download the source code from the upstream download servers or
repositories (or mirrors) only in the build process. The source is not added to
your source repository.

Without extra actions a buildroot or Yocto build is not source code
reproducable. If a upstream project shuts down it's infrastructure and there
are no mirrors maintained by other parties on the internet, you cannot
reproduce the build. You cannot redownload the source code.

That's why buildroot and Yocto have features like 

(TODO add)

But nevertheless it's an additional process/action you have to perform to
retain the source code of our dependencies on your own infrastructure.

Because upstream services can disappear Linux distirbution like debian maintain
their or copy/mirror of the source code for their packages.

TODO add link


# vendoring

TODO Explain


# reproducilbe builds

Apart from source code reproducabilty, there is also a property for the buid
process. It's called *reproducilbe builds*.

TODO explain, link to website


# hermetic builds

tdb


# atomic cross repository changes

tbd
