#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

# TODO reduce imports
import os
import unittest

from helpers import Git, TestCaseHelper, TestCaseTempFolder, cwd, touch


class TestGit(TestCaseTempFolder, TestCaseHelper):
    def test_apply(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()

            touch("fileA", b"A\n")
            git.add("fileA")
            git.commit("add fileA")

            touch("fileB", b"B\n")
            git.add("fileB")
            git.commit("add fileB")

            touch("fileA", b"C\n")
            git.add("fileA")
            git.commit("change fileA")

            git.call(["format-patch", "HEAD^^..", "-q"])
            self.assertFileExists("0001-add-fileB.patch")
            self.assertFileExists("0002-change-fileA.patch")

            # NOTE: patch files contain the version number of git. The host
            # systems that is running the tests, may have a different git
            # version installed.

            git_version = git.version()

            self.assertFileContent("0001-add-fileB.patch", b"""\
From 201213a1efdce5f80c9813df4150026f5bb885e0 Mon Sep 17 00:00:00 2001
From: OTHER other <other@example.com>
Date: Sat, 1 Oct 2016 14:00:00 +0800
Subject: [PATCH 1/2] add fileB

---
 fileB | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 fileB

diff --git a/fileB b/fileB
new file mode 100644
index 0000000..223b783
--- /dev/null
+++ b/fileB
@@ -0,0 +1 @@
+B
-- 
X.YY.Z

""".replace(b"X.YY.Z", git_version))

            self.assertFileContent("0002-change-fileA.patch", b"""\
From fe13031c85d23e297321dbcaf09fc4f3360923e6 Mon Sep 17 00:00:00 2001
From: OTHER other <other@example.com>
Date: Sat, 1 Oct 2016 14:00:00 +0800
Subject: [PATCH 2/2] change fileA

---
 fileA | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/fileA b/fileA
index f70f10e..3cc58df 100644
--- a/fileA
+++ b/fileA
@@ -1 +1 @@
-A
+C
-- 
X.YY.Z

""".replace(b"X.YY.Z", git_version))

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            touch("fileSuper", b"A\n")
            git.add("fileSuper")
            git.commit("first commit in super")

            # NOTE: Add this point actually "subpatch" would be used
            os.mkdir("subproject")
            touch("subproject/fileA", b"A\n")
            git.add("subproject/fileA")
            git.commit("add subproject")

            sha1 = git.get_sha1("HEAD:subproject")
            self.assertEqual(sha1, b"e5f76546416792cb5666efe82dadb5b0ff901f29")
            p = git.call(["ls-tree", "e5f76546416792cb5666efe82dadb5b0ff901f29"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
100644 blob f70f10e4db19068f79bc43844b49f3eece45c4e8\tfileA
""")

            # Testing apply
            # NOTE: If "--index" is not given and "apply" adds a new file in
            # the patch, It's not added to the index. So also in "git diff" not
            # visible!
            # NOTE: Adding multiple patches after another, works!

            # Applying the fist patch!
            git.call(["apply", "--index", "--directory=subproject", "../subproject/0001-add-fileB.patch"])
            p = git.call(["diff", "--name-status", "--staged"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
A\tsubproject/fileB
""")
            p = git.call(["write-tree"], capture_stdout=True)
            self.assertEqual(p.stdout, b"d11471c7f8adcc1220a4b24db11ab40eb39773ee\n")
            p = git.call(["diff", "HEAD", "d11471c7f8adcc1220a4b24db11ab40eb39773ee"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
diff --git a/subproject/fileB b/subproject/fileB
new file mode 100644
index 0000000..223b783
--- /dev/null
+++ b/subproject/fileB
@@ -0,0 +1 @@
+B
""")

            # Applying the second patch
            git.call(["apply", "--index", "--directory=subproject", "../subproject/0002-change-fileA.patch"])
            p = git.call(["diff", "--name-status", "--staged"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
M\tsubproject/fileA
A\tsubproject/fileB
""")
            p = git.call(["write-tree"], capture_stdout=True)
            self.assertEqual(p.stdout, b"61c1816e2634dcc06d7f4d05b6ae73870331708f\n")
            p = git.call(["diff", "HEAD", "61c1816e2634dcc06d7f4d05b6ae73870331708f"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
diff --git a/subproject/fileA b/subproject/fileA
index f70f10e..3cc58df 100644
--- a/subproject/fileA
+++ b/subproject/fileA
@@ -1 +1 @@
-A
+C
diff --git a/subproject/fileB b/subproject/fileB
new file mode 100644
index 0000000..223b783
--- /dev/null
+++ b/subproject/fileB
@@ -0,0 +1 @@
+B
""")

            git.commit("apply two patches")
            p = git.call(["ls-tree", "-r", "HEAD"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
100644 blob f70f10e4db19068f79bc43844b49f3eece45c4e8\tfileSuper
100644 blob 3cc58df83752123644fef39faab2393af643b1d2\tsubproject/fileA
100644 blob 223b7836fb19fdf64ba2d3cd6173c6a283141f78\tsubproject/fileB
""")

            # Get and check tree object of subproject
            p = git.call(["write-tree", "--prefix=subproject"], capture_stdout=True)
            self.assertEqual(p.stdout, b"b7578d59deec8f11a88b229c46f08e18321736bf\n")
            p = git.call(["ls-tree", "b7578d59deec8f11a88b229c46f08e18321736bf"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
100644 blob 3cc58df83752123644fef39faab2393af643b1d2\tfileA
100644 blob 223b7836fb19fdf64ba2d3cd6173c6a283141f78\tfileB
""")

            # git repo is in a sane state. all patches of the subproject are
            # added.
            #
            # Now deapply the patches again
            git.call(["apply", "--index", "--reverse", "--directory=subproject", "../subproject/0002-change-fileA.patch"])
            p = git.call(["write-tree"], capture_stdout=True)
            self.assertEqual(p.stdout, b"d11471c7f8adcc1220a4b24db11ab40eb39773ee\n")

            # Get and check tree object of subproject
            p = git.call(["write-tree", "--prefix=subproject"], capture_stdout=True)
            self.assertEqual(p.stdout, b"21dbeb1ed88507ddde7b189cdef82868543d1dcd\n")
            p = git.call(["ls-tree", "21dbeb1ed88507ddde7b189cdef82868543d1dcd"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
100644 blob f70f10e4db19068f79bc43844b49f3eece45c4e8\tfileA
100644 blob 223b7836fb19fdf64ba2d3cd6173c6a283141f78\tfileB
""")

            git.call(["apply", "--index", "--reverse", "--directory=subproject", "../subproject/0001-add-fileB.patch"])
            p = git.call(["write-tree"], capture_stdout=True)
            self.assertEqual(p.stdout, b"b7ff865de52afaacb3b9a714cc97aa4357c92f3b\n")

            # Get and check tree object of subproject
            # NOTE: This is the same tree SHA1 of the added subproject without patches
            p = git.call(["write-tree", "--prefix=subproject"], capture_stdout=True)
            self.assertEqual(p.stdout, b"e5f76546416792cb5666efe82dadb5b0ff901f29\n")
            p = git.call(["ls-tree", "e5f76546416792cb5666efe82dadb5b0ff901f29"], capture_stdout=True)
            self.assertEqual(p.stdout, b"""\
100644 blob f70f10e4db19068f79bc43844b49f3eece45c4e8\tfileA
""")


if __name__ == '__main__':
    unittest.main()
