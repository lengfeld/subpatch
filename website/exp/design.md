# subpatch design

subpatch is based on my experiences and learnings as a (embedded) software
engineer. Everything that I have seen and done in the last ten years feeds into
the following list of requirements.

*NOTE*: For now the implementation of subpatch not complete. Please read the
requirement list as a vision for the first major release of subpatch, not as a
status of the implementation.


## Requirements

The tool …

(**R1**) should support git, cvs, mercurial, subversion and non-cvs environment
as superprojects.

(**R2**) do not interfere with the vcs. The existing workflows
like checking out, cloning, switching branches, updating, rebasing, tagging,
forking, bisecting, releasing and ... should stay the same.

(**R3**) should support git, cvs, mercurial, subversion and source
code archives (like tarballs or zip files) as source dependencies/subprojects.

(**R4**) should track the original metadata (e.g. url, commit ids,
checksums, ... ) of the source dependency to verify the authenticity of the
dependency later.

(**R5**) should help integrating updates of the source dependencies.

(**R6**) should support local patching of source dependencies.

(**R7**) If the source dependency is patched locally, it should help
maintaining a linear patch stack.

(**R8**) When doing an update of a source dependency and there are no conflicts
with the local patches, the tool should rebase local patches automatically.

(**R9**) When doing an update of a source dependency and there are are conflicts
with the local patches, the tool should help porting the local patches.

(**R10**) should provided an stable command line API (plumbing commands) to
support other tools to track source dependencies, e.g. to automatically check
for updates or for CVEs.

(**R11**) Should support every development platform that also supports git and
python, like Linux, unixes, Windows and MacOS.

(**R12**) Should scale to the size of the AOSP (Android Open Source Project)


## Design decisions

The requirement list still gives a lot of freedom for the implementation.
Therefore I document and explain the chosen decisions here, while developing
subpatch.

(**DD1**): written in python3 (but open for a port to another language later if successful)

* [+] faster iteration speed
* [+] easier deployment/install of users. python runs everywhere.
* [+] programming language that I know really good and written a lot of code
  already.

(**DD2**): config file format is `git-config`

* [+] the same config format that the main cvs for subpatch (=git) uses.
* [+] Most developers are already familiar with the config format, e.g. because
  they are modyfing `~/.git config`.

*NOTE:* This list is not completed yet and should grow while supbatch is developed.
