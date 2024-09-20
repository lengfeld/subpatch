# Glossary

This page is a glossary. More important terms are at the top.


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

| Context            | Name for super*   | Name for sub*         |
| ------------------ | ----------------- | --------------------- |
| package manager    | project           | (source) dependencies |
| multi repo problem | superproject      | subprojects           |
| multi repo problem | super repository  | sub repositories      |
| multi repo problem | superrepo         | subrepos              |


## version control system (vcs)

A *version control system* is a tool to track changes to a set of files and provides
auxiliary functional. Sometimes these are also called *source code management* tools.

Popular version control systems are

* [git](https://git-scm.com/)
* [subversion (svn)](https://subversion.apache.org/)
* [mercurial](https://www.mercurial-scm.org/)
* [Concurrent Versions System (cvs)](http://savannah.nongnu.org/projects/cvs)
