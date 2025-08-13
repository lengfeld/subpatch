# Frequently asked questions

## What does the name *subpatch* mean?

The name subpatch consists of two parts: *sub* and *patch*

The term *sub* is inspired by `git submodules` and `git subtree`. Both use the
prefix `sub`, because the act on *sub*directories. subpatch does the same.
Third party dependencies (=subprojects) are added as subdirectories to the
superproject.

The second term *patch* stands for patching the source code. subpatch allows to
maintain a linear patch stack on top of the subproject. It's a unique
distinction for a multi repository management tool to promote it as a primary
feature like subpatch.  As far as I know, only kas also supports local
patching, but it's not a primary feature of it.


## subpatch is just another wrapper around git, right?

No, subpatch is not another wrapper around git. Like git submodules or git
subtree, subpatch is an extension to git.

Refere to the learning (L1) on [Learnings](learnings.md): The
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


## Does subpatch increase the storage requirements on the source control servers?

Yes, it does! But that is mostly good thing for you!

If you previously used git submodules, repo or other tools for our superproject and now
start to use subpatch, your repository will grow in size. The files of your
dependencies are directly in our repository (superproject) now. So they are
downloaded when you do a `git clone` or a co-worker does a `git fetch`.

In the case of git submodules, repo and other tools _and_ you have __not__
mirrored the subprojects on our own source control servers, you clone the
subprojects from the original upstream servers. So the files are not in your
repository on our server, but only in the upstream repositories.

So yes, the storage requirements on your source control servers increases.

But … it's mostly a good thing! Reasons:

* When using CI (continuous integration) and forgetting to configure a cache,
  git submodules, repo and others would continuously pull the dependencies from
  upstream. This increases the ingress traffic of your CI infrastructure and
  causes network traffic for the upstream project. That is not nice.
* When building a product, relying (open source) upstream to provide and
  maintaining the source code for a long time is risky. You should be able to
  reproduce the exact source code for compliance and bug-fixing reasons for all
  of your software releases.

And your local storage requirement on your development machine and in your CI
pipeline will __not__ change. Also git submodules, repo and others tools
download and checkout the subprojects, e.g. git repositories, for building the
software.

subpatch mostly will even reduce the storage size because of DD6: The history
of the upstream project is not included in the superproject. When using git
submodules, repo or others and you don't configure anything, git repositories
are not cloned with `--depth=1` by default. So you get the full history in your
local checkout.

## Subpatch makes the checkout bigger!

No, the whole checkout does not get larger. You have to take all the
dependencies or subprojects in your multi repository setup into account.

subpatch makes the checkout maybe even smaller. See previous answer.



## subpatch promotes vendoring of dependencies. I have heard that this is bad!

Yes and no.

TODO explain


## Are you a fan of monorepos?

Yes, I am (to some extend).

TODO Explain more.


## I'm using subpatch for my >200 GB source code project and I have git scaling issues now! What should I do?

Ok, that's an issue. But if you are at this scale, you should also have
resources in our organization to invest in better tooling. ;-)
