# Releases

This page lists all subpatch release with the release notes. The order is:
newest/latest releases are at the top, oldest releases are at the bottom. To
install subpatch, follow the steps in the
[installation tutorial](../tut/installation.md).

You always can download the latest standalone python script at the URL:
[https://subpatch.net/downloads/latest/subpatch](https://subpatch.net/downloads/latest/subpatch)

**Warning**: subpatch is in a very *very* early stage. Do not use it in
production environments! E.g. the config format will change. Nevertheless
please try it out. Any feedback is welcome.


## v0.1a3

Second release of subpatch.

Changes to the tool

* Adding support for the command line argument `-r | --revision` to the `add`
  command. This allows to checkout a specific branch, tag or commit or tag id
  for the subproject.
* Fix the limitation that only one subproject can be added to the superproject.
  Now the tool really starts to become usable to management multiple subprojects.

Changes to the website

* Adding a quick start guide to the [front page of the webpage](../index.md)
* Adding a [history page](../exp/history.md) to explain the path
  to subpatch and the learnings from previous attempts and projects
* Adding a reference for the [commandline arguments](command-line.md)
* Merging the website into the main git repository. This makes it easier to
  work on subpatch. The old
  [subpatch-website repo](https://github.com/lengfeld/subpatch-website) is archived
  now.

Further links:

* [github release page](https://github.com/lengfeld/subpatch/releases/tag/v0.1a3)
* standalone python script for download:
  [https://subpatch.net/downloads/v0.1a3/subpatch](https://subpatch.net/downloads/v0.1a3/subpatch)


## v0.1a2

First release of subpatch. For now it supports only two commands: `add` and
`status` with a very limited amount of functionality.

Further links:

* [github release page](https://github.com/lengfeld/subpatch/releases/tag/v0.1a2)
* standalone python script for download:
  [https://subpatch.net/downloads/v0.1a2/subpatch](https://subpatch.net/downloads/v0.1a2/subpatch)
