#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from contextlib import chdir
from os.path import abspath, dirname, join, realpath

from helpers import TestCaseTempFolder, Git, touch, create_and_chdir

path = realpath(__file__)
sys.path.append(join(dirname(path), "../src"))

# TODO rename "test_lib.py" to "test_main.py"
from super import (AppException, ErrorCode, FindSuperprojectData, SCMType,
                   check_superproject_data, find_superproject)


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


if __name__ == '__main__':
    unittest.main()
