# Learnings

On the previous [introductions page](intro.md), you could read about the basics
of the multi repository problem.

subpatch is not my first attempt to solve the multi repository problem. There
is a long history before I started the subpatch project. This page should tell
the history and what learnings I made along the way.

lt;dr: The summary of all learnings is

* (**L1**) The solution to the multi repository problem is inside of git
  (or generally inside any version control system).
* (**L2**) Good documentation is very very important.
* (**L3**) Good documentation with good tooling is the key.
* (**L4**) Use the right design to minimize the inherent complexity to avoid
   accidental complexity.
* (**L5**) The build process must stay inside of a single repository.
* (**L6**) The only sane way to maintain a downstream fork is a linear patch
  stack (=series of patches).
* (**L7**) Good development practices, like atomic commits, must still be
  possible with the multi repository management tool. Even across the used
  subprojects.


## Personal history

While writing these lines it's the year 2024. I started to use Linux in my
youth and also started to code at the same time. That is nearly 20 years in the
past now. So I may claim that I've been doing software development for 15+
years.

In university, around 2011, I started to write software as a research
assistant. Since 2014 (ten years) I've been doing embedded software development
as my main job and can call myself a professional software developer. In all these
years I have already seen a lot of programming languages, projects and problems.


## Multi repository problem (2015)

In 2015 at my first embedded software development job I encountered the multi
repository problem. The company was on the way to migrate the embedded build
system for their Linux distribution and firmware images to Yocto.

Back then I started to learn and use the [repo tool by
Google](https://gerrit.googlesource.com/git-repo) to manage projects with
multiple repositories.  While doing the first releases of the Linux firmware, I
noticed the weaknesses of using repo. Everything that is easy with a single
repository like

* checking out branches of a coworker,
* switching between different development branches (stable vs main),
* bisecting errors and
* making a release and tagging

becomes a major hassle with multiple repositories and the repo tool. And it's
very error prone. At that time I started a new hobby project called *rap*.


## The solution is inside a git repo (2015)

So I'm working on a better version of the repo, called *rap*, for three months.
It should be repo by Google done right. I wrote it in python and at the end it
consists of

* 2889 lines of code for the program and
*  985 lines of tests.

It should support features, like easy checkout of multiple repos, bisecting
across multiple repos and git bundles across multi repos.

After the three months I noticed that I was building a version control system
for git repositories. And git is itself a version control system. That is
duplicate and useless work. This brought me to the first learning:

(**L1**) The solution to the multi repository problem is **inside** of git (or
generally inside any version control system).

The solution is **not** writing a new version control system to manage version
control systems.

So I abandoned the rap project and looked at existing solutions that allow me
to manage multiple repositories inside a git repo. Most people know *git
submodules*, but there is also *git subtree*.


## Documentation, documentation and documentation (2015)

I already knew [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
and also knew that has its own set of usability challenges. So I looked at
[git subtree](https://git.kernel.org/cgit/git/git.git/tree/contrib/subtree/git-subtree.txt)
and its
[subtree merge strategy](https://mirrors.edge.kernel.org/pub/software/scm/git/docs/howto/using-merge-subtree.html).
Maybe it's a viable solution.

After trying it out I noticed that the documentation is lacking. I started to
write additional documentation for it and called the project *Handbook of
Applied git subtree merge*.

The problem is explaining the problem to developers and explaining how the
tool works to solve the management problem. This can be summarized up in the
learning:

(**L2**) Good documentation is very very important.

Quickly after that I also noticed that the tooling of git subtree is
inadequate. Only additional documentation will not fix usability issues.  The
third learning is:

(**L3**) Good documentation with good tooling is the key.


## Better Tooling (2016)

In 2016 I started to work on better tooling for git subtree. I called the
project *git-subtreemerge*. It should be git subtree done right. A better
tool to perform and help the user to use the subtree merge strategy of git.

I worked on this project from June 2016 to May 2017 (roughly eight months) in
my spare time. At the end the project consist of

* 5027 lines of python code for the program and
* 9544 lines of python code lines are tests.

So 65% percent of all the code are tests.

At this stage the basic features were working in the tool and I wanted to
release it as a prototype. So I started to work on the documentation that
explains how the tool works and the theory behind it.

I quickly noticed that this would not fly. It's not about the accidental
complexity of the git subtree merge strategy or the tool. It's about the
essential or inherent complexity of it. The core problem is that the merge
strategy is mixing commits of the subproject into the history (the commit
graph) of the superproject. If you have multiple subprojects, then you
also have multiple different types of subproject commits in the history
of the superproject.

Combine this with changes to the subproject in the superproject and combine
this with merges (different development branches) in the superproject, you get
a complexity explosion of everything that can happen and must be explained.
In fact there are mathematical underlying properties, embeddings and
commutative operations, for this. So in general it's sound.  But this setup is
not explainable to even experienced git users.

At this point I abandoned the project. My main learning was

(**L4**) Use the right design to minimize the inherent complexity to avoid
accidental complexity.

To phrase it for the git subtree merge strategy. It has a huge inherent
complexity, which is way too big for the essential complexity of the multi
repository management problem.


## Gerrit and repo (2018)

In 2018 I had the chance to work on a project that uses the [Gerrit Code Review
System](https://www.gerritcodereview.com/) together with the repo tool. I did
expect the same problems as in the year 2016, but gave the combination of
gerrit plus repo another try.

Summary: It's still madness. Even simple things like checking out the
branches of a coworker is non-trivial. It's not supported by the repo tool. We
started to implement our own tool called
[repoload](https://github.com/lengfeld/repoload) for that.

At least Gerrit supports submitting/accepting cross atomic commits.  That's a
feature you need when you start to distribute your project across multiple
git repos. The documentation
[Submitting Changes Across Repositories by using Topics](https://gerrit-review.googlesource.com/Documentation/cross-repository-changes.html).

So Gerrit has the cross repo atomic commit feature. Sadly our continuous
integration system (CI), Jenkins in this case, did not.  Our project rolled out its
own implementation based on the `Change-Id` and `Depends-On` fields in the
commit messages. Written in a combination of bash and groovy. Also madness.

There were a couple of other learnings from this project which I can summarize
up as:

(**L5**) The build process must stay inside of a single repository.

You can also phrase it differently. When you or your CI system must checkout
multiple git repos, that you own, for building the project, you are doing it
wrong.


## git add and linear patch stacks (2018+)

In the same project we used a different solution (not repo or git submodules)
for a small component.  We integrated a C++ dependency into the git repository
with `git add`. We just added the source files in a single commit into the
project. We even applied local patches to the project as normal git commits on
top of it.

When upgrading the dependency we removed the original files, added the new
source files and reapplied the patches with `git cherry-pick`. That process
worked nicely. The learning is:

(**L6**) The only sane way to maintain a downstream fork is a linear patch
stack (=series of patches).

And that is actually a very old thing. Linux distributions, like the big ones
for the desktop but also for embedded devices, maintain a linear patch stack
for their packages (=source dependencies). It's a process that has been done
for decades now.


## One last thing

One last learning that also feeds into subpatch is

(**L7**) Good development practices, like atomic commits, must still be
possible with the multi repository management tool. Even across the used
subprojects.


## Conclusion

That is my history of the multi repository problem. Hopefully it shows that the
following requirements and design decision are not an ad-hoc idea, but instead
based on a long period of experience and tackling the multi repository problem
from different angles.

If you want to find out more now, you can jump to the
[requirements page](requirements.md). Based on the learnings above it sketches
out the design of a new tool.
