# Benefits and drawbacks

This page lists all the benefits for you when you use subpatch instead of a
different solution.


## Easier to use than other solutions

No pitfalls like in repo or git-submodules

* easy branch swichting
* no git-submodules headeaches

And subpatch does the right thing for L4. It minimizes the accidentally
complexity.

There are different personas in an opensource project or software team. In a
simply view there are two different kinds of people. There are

* core developers or maintainers of a project and
* occassional contributors or distribution maintainers, just building the software.

With supbatch only the first group, the core developers, must have subpatch
install, know it's commands and use it.  So the people that are already more
knowledgeable about the project and are working full time on it.

For the occassional contributors or distribution maintainers, subpatch is at
first totally transparent. They can just checkout out the git repo or download
the tarball and build the software. They do _not_ need to know or learn
subpatch.

This is in heavy contrast to repo or git-submodules. For both even the later group must
understand repo or git submoudles and use it.


## Source code reproductabilty by design (=mirroring,=vendoring)

Since of DDX, the files of the subprojects are added directly to your source
control management system (=git). This means that you don't rely on the
availablity of servers or services of the upstream project. If a upstream
project shutsdown it download servers for the tarballs or removes their
repository on github, you still have all the source code for building all of
our software release. It's mirror by default in your scms.

For (license) compliance and security bug fixing it's a requirement to be able
to reproduce the source code and rebuild all or at least some of the latests
software releases.

If you use git submodules, repo or other tools _and_ you don't want to depend
on upstream, you have to implement our own mirror and infrastructure. With
subpatch you get it for free.


## No need for atomic cross repo change requests

* When using repo or git-submodules you want cross repo change requests
* Subpatch does not need it, because cross repo change requests are a pain (L1).
* There is no establied tooling for atomic cross repo change requests and it's
  a pain.


## Built-in patching

* For repo, git-submodules this needs forking/mirroring
* subpatch has this built-in an easy to use without hassel of extra repos.


## The right tradeoff for the subproject history

* The history of the subproject is not included in the superproject
* less clutter in the superproject history
* But still source code reproducible by default
* SHA1sums for reference to upstream saved in the metadata to restore it if
  necessary.


## Better caching and reduced ingress traffic

* no additional downloading in CI


## Better visiblity in size of upgrades of dependencies

* After `subpatch update`, you see the changes in `git diff`
* Package managers like yarn, npm, rust, hide the code changes


## Drawbacks

### Increased storage size on git forges/servers

* Since upstream source code is stored on your servers/orga by default with
  subpatch, the size increases. But this should be a good thing!


### Monorepo problems

* For very big projects, git does not scale well. But git has also improved.
  See Microsoft efforts!
