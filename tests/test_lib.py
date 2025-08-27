#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from os.path import abspath, dirname, join, realpath

from helpers import Git, TestCaseHelper, TestCaseTempFolder, cwd, touch

path = realpath(__file__)
sys.path.append(join(dirname(path), "../src"))

from main import (AppException, ErrorCode, FindSuperprojectData, SCMType,
                  URLTypes, check_superproject_data, config_add_subproject,
                  find_superproject, gen_sub_paths_from_cwd_and_relpath,
                  gen_sub_paths_from_relpath, gen_super_paths, get_url_type)


class TestConfigAddSubproject(TestCaseTempFolder, TestCaseHelper):
    def test_empty(self):
        touch(".subpatch", b"")
        config_add_subproject(b".subpatch", b"a/b/c")
        self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = a/b/c
""")

    def test_inserting(self):
        touch(".subpatch", b"""\
[core]
\tsome = setting
[subprojects]
\tpath = a/x
\tpath = c/x
""")
        config_add_subproject(b".subpatch", b"b/x")
        self.assertFileContent(".subpatch", b"""\
[core]
\tsome = setting
[subprojects]
\tpath = a/x
\tpath = b/x
\tpath = c/x
""")


class TestFindSuperproject(TestCaseTempFolder):
    def test_search_ends_on_filesystem_boundary(self):
        # NOTE: Assumption that "/run/" is a tmpfs and "/" is not!
        with cwd("/run/"):
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
        with cwd("a/b/c", create=True):
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
        with cwd("a/b/c", create=True):
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

        with cwd("a/b/c"):
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


class TestFuncs(unittest.TestCase):
    def test_get_url_type(self):
        self.assertEqual(URLTypes.REMOTE, get_url_type("https://xx"))
        self.assertEqual(URLTypes.REMOTE, get_url_type("http://xx"))
        self.assertEqual(URLTypes.REMOTE, get_url_type("git://xx"))
        self.assertEqual(URLTypes.REMOTE, get_url_type("ssh://xx"))
        self.assertEqual(URLTypes.LOCAL_RELATIVE, get_url_type("folder"))
        self.assertEqual(URLTypes.LOCAL_RELATIVE, get_url_type("sub/folder"))
        self.assertEqual(URLTypes.LOCAL_ABSOLUTE, get_url_type("/sub/folder"))

        self.assertRaises(NotImplementedError, get_url_type, "rsync://xx")
        self.assertRaises(ValueError, get_url_type, "")


class TestGenSuperPaths(TestCaseTempFolder):
    def test_multiple_level_of_subdirectories(self):
        super_abspath = os.getcwdb()
        paths = gen_super_paths(super_abspath)
        self.assertEqual(paths.super_abspath, super_abspath)
        self.assertEqual(paths.super_to_cwd_relpath, b"")

        with cwd("sub1", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1")

        with cwd("sub1/sub2", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2")

        with cwd("sub1/sub2/sub3", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2/sub3")

        with cwd("sub1/sub2/sub3/sub4", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2/sub3/sub4")


class TestGenSubPaths(TestCaseTempFolder):
    def test_gen_sub_paths_from_relpath(self):
        super_abspath = os.getcwdb()
        super_paths = gen_super_paths(super_abspath)

        sub_paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
        self.assertEqual(sub_paths.super_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(sub_paths.cwd_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(sub_paths.sub_name, b"sub2")

        with cwd("sub1", create=True):
            super_paths = gen_super_paths(super_abspath)
            sub_paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(sub_paths.cwd_to_sub_relpath, b"sub2")
            self.assertEqual(sub_paths.sub_name, b"sub2")

        with cwd("sub1/sub2", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3/sub4", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"../..")
            self.assertEqual(paths.sub_name, b"sub2")

        # Special case for sub_name: superproject at the toplevel directory
        super_paths = gen_super_paths(super_abspath)
        paths = gen_sub_paths_from_relpath(super_paths, b"")
        self.assertEqual(paths.super_to_sub_relpath, b"")
        self.assertEqual(paths.cwd_to_sub_relpath, b"")
        self.assertEqual(paths.sub_name, b"")

    def test_multiple_level_of_subdirectories(self):
        super_abspath = os.getcwdb()

        super_paths = gen_super_paths(super_abspath)
        paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"sub1/sub2")
        self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(paths.cwd_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"sub2")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"..")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3/sub4", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"../..")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"../..")
            self.assertEqual(paths.sub_name, b"sub2")

        # Special case for sub_name: superproject at the toplevel directory
        super_paths = gen_super_paths(super_abspath)
        paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"")
        self.assertEqual(paths.super_to_sub_relpath, b"")
        self.assertEqual(paths.cwd_to_sub_relpath, b"")
        self.assertEqual(paths.sub_name, b"")

    def test_argument_is_normalized(self):
        super_abspath = os.getcwdb()
        super_paths = gen_super_paths(super_abspath)

        with cwd("sub1/sub2/", create=True):
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"..")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")

            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"../.")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")

            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b".")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")


if __name__ == '__main__':
    unittest.main()
