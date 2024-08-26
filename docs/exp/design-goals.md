# Design Goals

subpatch is designed based on the following goals. The tool subpatch

1. is vcs agnostic, but integrates with the vcs
2. allows local patching/forking of subprojects
3. does interfere with the vcs
    1. is distributed (as in git)
    2. allows nesting
4. does not mix build tool and vcs
5. puts the complexity at the right sport (tb)
