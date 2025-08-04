# Frequently asked questions

## What does the name *subpatch* mean?

The name subpatch consists of two parts: *sub* and *patch*

The term *sub* is inspired by `git submodules` and `git subtree`. Both use the
prefix `sub`, because the act on *sub*directories. subpatch does the same.
Third party dependencies (=subprojects) are added as subdirectories to the
superproject.

The second term *patch* stands for patching the source code. subpatch allows to
maintain a linear patch stack on top of the subproject. As far as I know, this
is a unique feature for multi repository management tools like subpatch.


## Subpatch is just another wrapper around git, right?

No, subpatch is not another wrapper around git. Like git submodules or git
subtree, subpatch is an extension to git.

Refere to the learning (L1) on [Pre-subpatch history](history.md): The
solution to the multi repository problem is inside of git (or generally inside
any version control system).

E.g., look at two common operations for SCM tools: tagging and switches
branches. For subpatch `git switch` and `git tag` just work as before. When
tagging a release, all source code files and all subprojects are tagged with a
single command and a single tag. Same for `git switch`. With the same command,
all source code files and all subprojects are switched to a different branch.

Now look at the repo tool, which I call a wrapper around git. How does tagging
work? There is no single command to tag the whole superproject. You have to
perform multiple steps

    $ repo forall git tag -a ... # tag all subprojects individually
    $ repo forall git push <remote name> <tagname>

    # Now continue in the manifest repository
    $ cd ../manifest-repo
    $ vim manifest.xml  # replace default revision with newly create tag
    $ git commit -a -m "add tag in release manifest"
    $ git push origin HEAD:refs/heads/release-xy

So just making a release, consists of multiple steps. And the whole process is
error prone and not atomic. If you make a error somewhere, there is no easy way
to roll back everything.

It's the same issue apply when switching branches. The repo tool does not
support an easy way to checkout the branches of pull request/merged. For that
some of my coworkers and I coded our own tool. See
[repoload](https://github.com/lengfeld/repoload).

That's why I call repo and other tools "a wrapper around git", because existing
features of a SCM tool are reimplemented or need to be reimplemented. And
subpatch is carefully designed to not be a wrapper around git.
