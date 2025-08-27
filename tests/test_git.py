#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from os.path import join, dirname, realpath
from helpers import (Git, TestCaseHelper, TestCaseTempFolder, cwd, touch,
                     create_git_repo_with_branches_and_tags, mkdir)

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from src.git import (get_name_from_repository_url,
                     git_diff_in_dir, git_diff_name_only,
                     git_get_object_type, git_get_sha1, git_get_toplevel,
                     git_init_and_fetch, git_ls_files_untracked,
                     git_ls_remote, git_ls_remote_guess_ref,
                     git_ls_tree_in_dir, git_verify, is_sha1,
                     is_valid_revision, parse_sha1_names, parse_z, ObjectType)


class TestGit(TestCaseTempFolder):
    def test_get_name_from_repository_url(self):
        f = get_name_from_repository_url
        self.assertEqual("name", f("name"))
        self.assertEqual("name", f("/name/"))
        self.assertEqual("name", f("/name/.git/"))
        self.assertEqual("name", f("/name/.git"))
        self.assertEqual("name", f("/name.git"))
        self.assertEqual("name", f("/name.git/"))
        self.assertEqual("name", f("sub/name.git/"))
        self.assertEqual("name", f("http://localhost:7000/name/.git/"))

    def test_is_valid_revision(self):
        self.assertTrue(is_valid_revision("main"))
        self.assertTrue(is_valid_revision("refs/heads/main"))
        self.assertTrue(is_valid_revision("v1.1"))
        self.assertTrue(is_valid_revision("177324cdffb43c57471674a4655a2a513ab158f5"))
        self.assertFalse(is_valid_revision("main\nxx"))
        self.assertFalse(is_valid_revision("main\tx"))
        self.assertFalse(is_valid_revision("\bmain"))

    def test_parse_z(self):
        self.assertEqual([], parse_z(b""))
        self.assertEqual([b""], parse_z(b"\0"))
        self.assertEqual([b"xx", b"yy"], parse_z(b"xx\0yy\0"))

    def test_is_sha1(self):
        self.assertTrue(is_sha1(b"32c32dcaa3c7f7024387640a91e98a5201e1f202"))
        self.assertFalse(is_sha1(b".2c32dcaa3c7f7024387640a91e98a5201e1f202"))

    def test_git_get_object_type(self):
        git = Git()
        git.init()
        touch("file", b"content")
        git.add("file")
        git.commit("message")
        git.tag("v1", "msg")

        self.assertEqual(ObjectType.COMMIT, git_get_object_type(b"HEAD"))
        self.assertEqual(ObjectType.TREE, git_get_object_type(b"HEAD^{tree}"))
        self.assertEqual(ObjectType.BLOB, git_get_object_type(b"HEAD:file"))
        self.assertEqual(ObjectType.TAG, git_get_object_type(b"v1"))
        # TODO Catching the generic 'Exception' is bad. The code should use a
        # custom execption!
        self.assertRaises(Exception, git_get_object_type, b"vdoes-not-exists")

    def test_git_get_toplevel_not_in_git_folder(self):
        self.assertIsNone(git_get_toplevel())

    def test_git_get_toplevel(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()
            touch("hello", b"content")
            git.add("hello")
            git.commit("msg")

            cur_cwd = os.getcwdb()
            git_path = git_get_toplevel()
            self.assertEqual(git_path, cur_cwd)
            self.assertTrue(git_path.endswith(b"/subproject"))

            with cwd("test", create=True):
                # It's still the toplevel dir, not the subdir "test"
                git_path = git_get_toplevel()
                self.assertEqual(git_path, cur_cwd)
                self.assertTrue(git_path.endswith(b"/subproject"))

    def test_git_init_and_fetch(self):
        with cwd("remote", create=True):
            create_git_repo_with_branches_and_tags()

        with cwd("local", create=True):
            sha1 = git_init_and_fetch("../remote", "refs/tags/v1.1")
            self.assertEqual(b"e85c40dcd26466c0052323eb767d1a44ef0a12c1", sha1)
            self.assertEqual(ObjectType.TAG, git_get_object_type(sha1))

            sha1 = git_init_and_fetch("../remote", "refs/heads/v1-stable")
            self.assertEqual(b'32c32dcaa3c7f7024387640a91e98a5201e1f202', sha1)
            self.assertEqual(ObjectType.COMMIT, git_get_object_type(sha1))

            # TODO replace with specific git exception
            self.assertRaises(Exception, git_init_and_fetch,
                              "../remote", "refs/heads/does_not_exists")

    def test_depth_for_git_init_and_fetch(self):
        with cwd("remote", create=True):
            git = Git()
            git.init()
            touch("file", b"a")
            git.add("file")
            git.commit("first commit")
            sha1_first_commit = git.get_sha1()
            sha1_first_tree = git.get_sha1("HEAD^{tree}")
            sha1_first_blob = git.get_sha1("HEAD:file")

            touch("file", b"b")
            git.add("file")
            git.commit("second commit")
            sha1_second_commit = git.get_sha1()
            sha1_second_tree = git.get_sha1("HEAD^{tree}")
            sha1_second_blob = git.get_sha1("HEAD:file")

        with cwd("local", create=True):
            git = Git()
            git.init()
            sha1 = git_init_and_fetch("../remote", "refs/heads/master")
            self.assertEqual(sha1, b"b8019be749b96c92c65ae2fdb99753670fd32cf9")

            # The top most (depth=1) objects are exist in the object store.
            self.assertTrue(git.object_exists(sha1_second_blob))
            self.assertTrue(git.object_exists(sha1_second_tree))
            self.assertTrue(git.object_exists(sha1_second_commit))

            # The other objects (depth>=2) objects do not exist in the object
            # store.
            self.assertFalse(git.object_exists(sha1_first_blob))
            self.assertFalse(git.object_exists(sha1_first_tree))
            self.assertFalse(git.object_exists(sha1_first_commit))

    def test_git_ls_remote(self):
        with cwd("remote", create=True):
            create_git_repo_with_branches_and_tags()
            refs_sha1 = git_ls_remote(".")
        self.assertEqual([b'HEAD',
                          b'refs/heads/main', b'refs/heads/v1-stable',
                          b'refs/tags/v1', b'refs/tags/v1^{}',
                          b'refs/tags/v1.1', b'refs/tags/v1.1^{}',
                          b'refs/tags/v2', b'refs/tags/v2^{}'],
                         list(refs_sha1))
        self.assertEqual(b"60c7ec01d2a8d8c450896bb683c16637d52ea63c",
                         refs_sha1[b"refs/tags/v2"])
        self.assertEqual(b"e85c40dcd26466c0052323eb767d1a44ef0a12c1",
                         refs_sha1[b"refs/tags/v1.1"])

    def test_parse_sha1_names(self):
        self.assertEqual(parse_sha1_names(b"""\
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\tHEAD
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/heads/main
cccccccccccccccccccccccccccccccccccccccc\trefs/tags/v0.1a2
dddddddddddddddddddddddddddddddddddddddd\trefs/tags/v0.1a2^{}
""", sep=b"\t"), {b"HEAD": b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                  b"refs/heads/main": b"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                  b"refs/tags/v0.1a2": b"cccccccccccccccccccccccccccccccccccccccc",
                  b"refs/tags/v0.1a2^{}": b"dddddddddddddddddddddddddddddddddddddddd",
                  })

        # Empty file
        self.assertEqual(parse_sha1_names(b""), {})

        # With empty lines
        self.assertEqual(parse_sha1_names(b"\n\n\n"), {})

    def test_git_ls_remote_guess_ref(self):
        with cwd("remote", create=True):
            create_git_repo_with_branches_and_tags()

            self.assertEqual(b"refs/heads/main",
                             git_ls_remote_guess_ref(".", "main"))
            self.assertEqual(b"refs/heads/main",
                             git_ls_remote_guess_ref(".", "refs/heads/main"))
            self.assertEqual(b"refs/tags/v1",
                             git_ls_remote_guess_ref(".", "v1"))
            self.assertEqual(None, git_ls_remote_guess_ref(".", "v3"))

    def test_git_verify(self):
        # TODO Exception should be replaced with a git specifc exception
        self.assertRaises(Exception, git_verify, "main")

        create_git_repo_with_branches_and_tags()
        self.assertEqual(True, git_verify("main"))
        self.assertEqual(False, git_verify("does-not-exists"))
        self.assertEqual(True, git_verify("v1"))
        self.assertEqual(True, git_verify("refs/tags/v1.1"))
        self.assertEqual(False, git_verify("00" * 20))

    def test_git_diff_name_only(self):
        git = Git()
        git.init()

        # NOTE: Only tracked and changed files are shown in "git diff"
        # Untracked files are not listed in "git diff"
        touch("a")
        git.add("a")
        git.commit("test")
        touch("a", b"x")
        self.assertEqual([b"a"], git_diff_name_only())
        self.assertEqual([], git_diff_name_only(staged=True))

        mkdir("b")
        touch("b/c")
        git.add("b/c")
        git.commit("test")
        touch("b/c", b"x")
        # 'a' has committed changes
        self.assertEqual([b"a", b"b/c"], git_diff_name_only())
        self.assertEqual([], git_diff_name_only(staged=True))

        git.add("a")
        self.assertEqual([b"b/c"], git_diff_name_only())
        self.assertEqual([b"a"], git_diff_name_only(staged=True))
        git.add("b/c")
        self.assertEqual([], git_diff_name_only())
        self.assertEqual([b"a", b"b/c"], git_diff_name_only(staged=True))

    def test_git_ls_files_untracked(self):
        git = Git()
        git.init()

        self.assertEqual([], git_ls_files_untracked())

        touch("a")
        self.assertEqual([b"a"], git_ls_files_untracked())

        touch("b")
        self.assertEqual([b"a", b"b"], git_ls_files_untracked())

        # Make the untracked file a tracked file
        git.add("a")
        # Now only one file is untracked
        self.assertEqual([b"b"], git_ls_files_untracked())

        # Make a untracked file that is ignored with gitignore
        touch("c")
        touch(".gitignore", b"c\n")
        git.add(".gitignore")
        # It should not show up in the untracked files list!
        self.assertEqual([b"b"], git_ls_files_untracked())

        # Create a untracked file in a directory
        with cwd("subdir", create=True):
            touch("d")

        # NOTE: The config for "ls-files" only shows untracked dirs, not the
        # untracked files in the dirs.
        self.assertEqual([b"b", b"subdir/"], git_ls_files_untracked())

        with cwd("subdir"):
            # TODO: This is bad. It does not show the file "b" that is
            # untracked in the root of the git repo
            # "git ls-files" depends on the current work directory
            self.assertEqual([b"subdir/"], git_ls_files_untracked())

    def test_git_ls_files_untracked_ignore_files_in_di(self):
        # Special case found in the wild
        # git_ls_files_untracked() should not print directories that do only
        # contain ignored files. Happend with "__pycache__" dirs.
        git = Git()
        git.init()

        with cwd("__pycache__", create=True):
            touch("subpatch.cpython-310.pyc", b"something")
        self.assertEqual([b"__pycache__/"], git_ls_files_untracked())

        # Now make the file in the untracked directory ignored
        touch(".gitignore", b"*.pyc\n")
        git.add(".gitignore")
        git.commit("add gitignore")
        # And it's not listed anymore. Great!
        self.assertEqual([], git_ls_files_untracked())

    def test_git_diff_in_dir(self):
        git = Git()
        git.init()
        top_dir = os.getcwdb()

        mkdir("dir")
        touch("dir/a")
        touch("b")
        git.add("dir/a")
        git.add("b")
        git.commit("add a and b")

        # Without any changes
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With unstaged changes in other part of the repo
        touch("b", b"changes")
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With staged changes in other part of the repo
        git.add("b")
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With unstaged changes in the subdir
        touch("dir/a", b"changes")
        self.assertTrue(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertTrue(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With staged changes in the subdir
        git.add("dir/a")
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertTrue(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertTrue(git_diff_in_dir(top_dir, "dir", staged=True))

    def test_git_ls_tree_in_dir(self):
        git = Git()
        git.init()

        mkdir("dir")
        touch("dir/a")
        touch("b")
        git.add("dir/a")
        git.add("b")
        git.commit("add a and b")

        self.assertEqual([b"b", b"dir/a"], git_ls_tree_in_dir(b""))
        self.assertEqual([b"dir/a"], git_ls_tree_in_dir(b"dir"))
        self.assertEqual([], git_ls_tree_in_dir(b"does-not-exists-dir"))

        # If the cwd is a subdirectory, the output and the argument are still
        # relative to the toplevel of the repository.
        with cwd("dir"):
            self.assertEqual([b"b", b"dir/a"], git_ls_tree_in_dir(b""))
            self.assertEqual([b"dir/a"], git_ls_tree_in_dir(b"dir"))
            self.assertEqual([], git_ls_tree_in_dir(b"does-not-exists-dir"))

    def test_git_get_sha1(self):
        git = Git()
        git.init()
        git.call(["switch", "-c", "main", "-q"])

        touch("a", b"1")
        git.add("a")
        git.commit("add a")
        git.tag("v1", "msg")

        touch("a", b"2")
        git.add("a")
        git.commit("change a")

        self.assertEqual(git_get_sha1("HEAD"), b"4975f72e17be27d5e0d66dd3ec6ea9662de9046e")
        self.assertEqual(git_get_sha1("HEAD^"), b"e9a39bbb7a5057ad81ae413ed9b31a848e73b36a")
        self.assertEqual(git_get_sha1("v1"), b"e3471ab3cc16a5dc71317a5567929f172a88d763")
        self.assertEqual(git_get_sha1("main"), b"4975f72e17be27d5e0d66dd3ec6ea9662de9046e")


class TestGitPatching(TestCaseTempFolder, TestCaseHelper):
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
