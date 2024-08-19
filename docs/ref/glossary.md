# Glossary

This page is a glossary. More important terms are at the top.

## superproject

The superproject is the parent project in a multi repository setup. It's often
a git repository itself, e.g. for `git submodule`. When using subpatch the
superproject has the configuration file `.subpatch` at its top level directory.

## subproject

The subproject or subprojects are the external projects, often called third
party dependencies, that are added to the superproject.

*Note*: The terms *super-* and *sub-*projects are always relative to a specific
project setup. It might be the case that the superproject of a project (e.g. a
C library with third party dependencies) is the subproject of another project
(e.g. a C++ application, using the library).
