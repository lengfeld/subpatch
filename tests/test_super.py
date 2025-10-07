#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from contextlib import chdir
from os.path import abspath, dirname, join, realpath

from helpers import TestCaseTempFolder, Git, touch, create_and_chdir, mkdir

path = realpath(__file__)
sys.path.append(join(dirname(path), "../src"))

# TODO rename "test_lib.py" to "test_main.py"
from git import git_cat_file_pretty
from super import (AppException, ErrorCode, FindSuperprojectData, SCMType,
                   check_superproject_data, find_superproject, SuperHelperGit)


class TestFindSuperproject(TestCaseTempFolder):
    def test_search_ends_on_filesystem_boundary(self):
        # NOTE: Assumption that "/run/" is a tmpfs and "/" is not!
        with chdir("/run/"):
            # TODO find a way to test this. The abort was done because the
            # filesystem boundary was hit!
            data = find_superproject()
            self.assertEqual(data.super_path, None)
            self.assertEqual(data.scm_type, None)
            self.assertEqual(data.scm_path, None)

    def test_plain_superproject(self):
        # No configuration file in the path.
        abs_cwd = abspath(os.getcwdb())
        data = find_superproject()
        self.assertEqual(data.super_path, None)
        self.assertEqual(data.scm_type, None)
        self.assertEqual(data.scm_path, None)

        # A configuration file at the current work directory
        touch(".subpatch")
        data = find_superproject()
        self.assertEqual(data.super_path, abs_cwd)
        self.assertEqual(data.scm_type, None)
        self.assertEqual(data.scm_path, None)

        # A configuration file at a toplevel directory
        with create_and_chdir("a/b/c"):
            data = find_superproject()
            self.assertEqual(data.super_path, abs_cwd)
            self.assertEqual(data.scm_type, None)
            self.assertEqual(data.scm_path, None)

    def test_git_superproject(self):
        abs_cwd = abspath(os.getcwdb())
        git = Git()
        git.init()
        data = find_superproject()
        self.assertEqual(data.super_path, None)
        self.assertEqual(data.scm_type, SCMType.GIT)
        self.assertEqual(data.scm_path, abs_cwd)

        # Now check in a subdirectory
        with create_and_chdir("a/b/c"):
            data = find_superproject()
            self.assertEqual(data.super_path, None)
            self.assertEqual(data.scm_type, SCMType.GIT)
            self.assertEqual(data.scm_path, abs_cwd)

        # Now check with a configuration file
        touch(".subpatch")
        data = find_superproject()
        self.assertEqual(data.super_path, abs_cwd)
        self.assertEqual(data.scm_type, SCMType.GIT)
        self.assertEqual(data.scm_path, abs_cwd)

        with chdir("a/b/c"):
            data = find_superproject()
            self.assertEqual(data.super_path, abs_cwd)
            self.assertEqual(data.scm_type, SCMType.GIT)
            self.assertEqual(data.scm_path, abs_cwd)
            # Adding the subpatch config file makes it a PLAIN superproject.
            # TODO E.g. think about a superproject including a project that
            # uses subpatch.
            touch(".subpatch", b"")
            abs_cwd_sub = abspath(os.getcwdb())
            data = find_superproject()
            self.assertEqual(data.super_path, abs_cwd_sub)
            self.assertEqual(data.scm_type, SCMType.GIT)
            self.assertEqual(data.scm_path, abs_cwd)


class TestCheckSuperprojectData(TestCaseTempFolder):
    def test_no_scm_and_no_config(self):
        data = FindSuperprojectData(None, None, None)
        checked_data = check_superproject_data(data)
        self.assertIsNone(checked_data)

    def test_config_and_no_scm(self):
        data = FindSuperprojectData(b"/super", None, None)
        checked_data = check_superproject_data(data)
        self.assertEqual(checked_data.super_path, b"/super")
        self.assertEqual(checked_data.configured, True)
        self.assertEqual(checked_data.scm_type, None)

    def test_config_and_scm(self):
        data = FindSuperprojectData(b"/super", SCMType.GIT, b"/super")
        checked_data = check_superproject_data(data)
        self.assertEqual(checked_data.super_path, b"/super")
        self.assertEqual(checked_data.configured, True)
        self.assertEqual(checked_data.scm_type, SCMType.GIT)

    def test_no_config_and_scm(self):
        data = FindSuperprojectData(None, SCMType.GIT, b"/super")
        checked_data = check_superproject_data(data)
        self.assertEqual(checked_data.super_path, b"/super")
        self.assertEqual(checked_data.configured, False)
        self.assertEqual(checked_data.scm_type, SCMType.GIT)

    def test_missmatch_path(self):
        with self.assertRaises(AppException) as context:
            data = FindSuperprojectData(b"/a", SCMType.GIT, b"/b")
            check_superproject_data(data)
        self.assertEqual(context.exception.get_code(), ErrorCode.NOT_IMPLEMENTED_YET)


class TestSuperHelperGit(TestCaseTempFolder):
    def test_get_sha1_for_subtree(self):
        git = Git()
        git.init()

        mkdir("subproject")
        touch("subproject/hello")
        mkdir("subproject/subdir")
        touch("subproject/subdir/hello")
        mkdir("subproject/patches")
        touch("subproject/patches/0001-x.patch")
        touch("subproject/.subproject")

        git.add("subproject")
        git.commit("add subproject")

        # And also have one file in the index that is not committed yet. This
        # is a edgecase we rely on.
        touch("subproject/file-in-index")
        git.add("subproject")

        super_helper = SuperHelperGit()

        super_to_sub_relpath = b"subproject"

        sha1 = super_helper.get_sha1_for_subtree(super_to_sub_relpath)
        self.assertEqual(sha1, b"084636915836537663748269699d8f0cbfa5983d")
        self.assertEqual(git_cat_file_pretty(b"084636915836537663748269699d8f0cbfa5983d"), b"""\
100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391\tfile-in-index
100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391\thello
040000 tree f966952d7e0715683ee935d201cd4ab22736c831\tsubdir
""")

    def test_get_diff_for_subtree(self):
        git = Git()
        git.init()

        mkdir("subproject")
        touch("subproject/hello")
        mkdir("subproject/subdir")
        touch("subproject/subdir/hello")
        mkdir("subproject/patches")
        touch("subproject/patches/0001-x.patch")
        touch("subproject/.subproject")

        git.add("subproject")
        git.commit("add subproject")

        # And also have one file in the index that is not committed yet. This
        # is a edgecase we rely on.
        touch("subproject/file-in-index", b"content-of-file-in-index\n")
        git.add("subproject")

        super_helper = SuperHelperGit()

        super_to_sub_relpath = b"subproject"

        subtree_diff = super_helper.get_diff_for_subtree(super_to_sub_relpath)
        self.assertEqual(subtree_diff, b"""\
diff --git a/file-in-index b/file-in-index
new file mode 100644
index 0000000..54d8917
--- /dev/null
+++ b/file-in-index
@@ -0,0 +1 @@
+content-of-file-in-index
""")


if __name__ == '__main__':
    unittest.main()
