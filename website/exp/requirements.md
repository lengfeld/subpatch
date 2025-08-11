# Requirements

I based subpatch on my experiences and learnings as a (embedded) software
engineer. Everything that I have seen and done in the last ten years feeds into
the following list of requirements. See the [learnings](learnings.md) for
details.

*Note*: For now the implementation of subpatch not complete. Please read the
requirement list as a vision for the first major release of subpatch, not as a
status of the implementation.


## List of requirements

The tool …

(**R1**) should support git as the primary scm tool for the superproject and
cvs, mercurial, subversion and non-scm environment as functional but limited
superprojects.

(**R2**) do not interfere with the vcs. The existing workflows
like checking out, cloning, switching branches, updating, rebasing, tagging,
forking, bisecting, releasing and … should stay the same.

(**R3**) should support git, cvs, mercurial, subversion and source
code archives (like tarballs or zip files) as source dependencies/subprojects.

(**R4**) should track the original metadata (e.g. url, commit ids,
checksums, … ) of the source dependency to verify the authenticity of the
dependency later.

(**R5**) should help integrating updates of the source dependencies.

(**R6**) should support local patching of source dependencies.

(**R7**) If the source dependency is patched locally, it should help
maintaining a linear patch stack.

(**R8**) should rebase local patches automatically, when doing an update of a
source dependency and there are *no conflicts* with the local patches.

(**R9**) should help porting the local patches, when doing an update of a
source dependency and there are *conflicts* with the local patches.

(**R10**) should provided an stable command line API (plumbing commands) to
support other tools to track source dependencies, e.g. to automatically check
for updates or for CVEs.

(**R11**) should support every development platform that also supports git and
python, like Linux, unixes, Windows and MacOS.

(**R12**) should scale to the size of the AOSP (Android Open Source Project).


## Conclusion

The list of requirements is the design goal of subpatch. It describes the
properties and capabilities an implementation should fulfil and provide for its
users.

If you want to find more about the development and implementation, you can
continue reading on the page [design decisions](design.md).


## Change history

Update to *R1* on 2025-01-12: subpatch only supports git as a superproject with
all features.

Background: The requirement R1 was modified. Not all scm tools are supported
fully anymore.  The full functionality will only be available if the
superproject is a git repository.

Reasons: Avoid rewriting existing functionality, e.g. applying patches,
calculating a tree checksum, maintaining and listing tracked (and non-tracked)
files. If the superproject is not git or not a scm at all, these functions need
to be implemented in subpatch. Why reimplementing existing functionality?

This learning I had already in the past. See learning L1 on
[learnings](learnings.md): The solution is inside a scm tool. subpatch should not
try or need to reimplementing existing functionality.
