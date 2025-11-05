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

(**R1**) do not interfere with the vcs. The existing workflows
like checking out, cloning, switching branches, updating, rebasing, tagging,
forking, bisecting, releasing and … should stay the same.

(**R2**) should support git as the primary scm tool for the superproject and
cvs, mercurial, subversion and non-scm environment as functional but limited
superprojects.

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

(**R13**) should allow conflict free merging of subproject changes when
the changes are independent.

TODO: The text above uses the term *source dependencies*. Maybe use the terms
*subproject* and *upstream* to make the text clearer.  These terms are the
common terms in the subpatch nomenclature.


## Change history

### Update to R2 on 2025-01-12

Change: subpatch only supports git as a superproject with all features.

Background: The requirement R2 was modified. Not all scm tools are supported
fully anymore.  The full functionality will only be available if the
superproject is a git repository.

Reasons: Avoid rewriting existing functionality, e.g. applying patches,
calculating a tree checksum, maintaining and listing tracked (and non-tracked)
files. If the superproject is not git or not a scm at all, these functions need
to be implemented in subpatch. Why reimplementing existing functionality?

This learning I had already in the past. See learning L1 on
[learnings](learnings.md): The solution is inside a scm tool. subpatch should not
try or need to reimplementing existing functionality.


### Adding R13 on 2025-11-05

After a discussion with a friend and potential user of subpatch I added this
requirement. No other requirement specifies this and I even made a design
decision in the code that violates this feature.

But I think it's an important property and is needed. If two developers are
adding patches to the subproject _and_ these patches are independent, the merge
of these two development branches should be conflict free and afterwards the
subproject should be in a clean/valid state. The term *independent* for patches
means that the patches modify different source code parts and the changes are
in itself conflict free. In that case there should be also no conflict in the
subprojects metadata. The simple and common case should work automagically.

If the patches are _not_ conflict free (= not independent), the merge of the
code changes is a conflict already and must be resolved by the developers
manually. That's o.k. and expected. That is the same case if the source
code is maintained as a normal git repository and not as a subproject.


## Conclusion

The list of requirements is the design goal of subpatch. It describes the
properties and capabilities an implementation should fulfil and provide for its
users.

If you want to find out more about the difference to other tools, see
[comparison to other tools](comparison.md). The page gives on overview about
the other existing tools and compares them with subpatch.
