#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from contextlib import chdir
from os.path import dirname, join, realpath

from helpers import (TestCaseHelper, TestCaseTempFolder, create_and_chdir,
                     touch)

path = realpath(__file__)
sys.path.append(join(dirname(path), "../src"))

from util import AppException, ErrorCode
from main import (config_add_subproject, gen_sub_paths_from_cwd_and_relpath,
                  gen_sub_paths_from_relpath, gen_super_paths, read_metadata,
                  Metadata, checks_for_cmds_with_single_subproject)


class TestReadMetadata(TestCaseTempFolder, TestCaseHelper):
    def test_empty(self):
        touch(".subproject", b"")
        self.assertEqual(read_metadata(".subproject"),
                         Metadata(None, None, None, None, None))

    def test_all_data(self):
        touch(".subproject", b"""\
[patches]
\tappliedIndex = -1
[subtree]
\tchecksum = 202864b6621f6ed6b9e81e558a05e02264b665f3
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\trevision = 32c32dcaa3c7f7024387640a91e98a5201e1f202
\turl = ../subproject
""")
        self.assertEqual(read_metadata(".subproject"),
                         Metadata(b"../subproject",
                                  b"32c32dcaa3c7f7024387640a91e98a5201e1f202",
                                  b"c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c",
                                  b"-1",
                                  b"202864b6621f6ed6b9e81e558a05e02264b665f3"))


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


class TestGenSuperPaths(TestCaseTempFolder):
    def test_multiple_level_of_subdirectories(self):
        super_abspath = os.getcwdb()
        paths = gen_super_paths(super_abspath)
        self.assertEqual(paths.super_abspath, super_abspath)
        self.assertEqual(paths.super_to_cwd_relpath, b"")

        with create_and_chdir("sub1"):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1")

        with create_and_chdir("sub1/sub2"):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2")

        with create_and_chdir("sub1/sub2/sub3"):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2/sub3")

        with create_and_chdir("sub1/sub2/sub3/sub4"):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2/sub3/sub4")


class TestChecksForCmdsWithSingleSubproject(TestCaseTempFolder):
    def test_two_subprojects_with_same_prefix(self):
        # TODO This test sets up the config and metadata files manually. There
        # are maybe errors or inconsistencies here. Add a subpatch check
        # command to verfiy that they are correct and consistent.
        touch(".subpatch", b"""\
[subprojects]
\tpath = subproject
\tpath = subproject-second
""")
        os.mkdir(".git")
        os.mkdir("subproject")
        os.mkdir("subproject/subdir")
        touch("subproject/.subproject", b"")
        os.mkdir("subproject-second")
        os.mkdir("subproject-second/subdir")
        touch("subproject-second/.subproject", b"")

        with chdir("subproject"):
            superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()
            self.assertEqual(super_paths.super_to_cwd_relpath, b"subproject")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"subproject")
        with chdir("subproject/subdir"):
            with self.assertRaises(AppException) as context:
                checks_for_cmds_with_single_subproject(enforce_cwd_is_subproject=True)
            self.assertEqual(context.exception.get_code(), ErrorCode.INVALID_ARGUMENT)
            self.assertEqual(str(context.exception), "Current work directory must be the toplevel directory of the subproject for now!")

        with chdir("subproject/subdir"):
            superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject(enforce_cwd_is_subproject=False)
            self.assertEqual(super_paths.super_to_cwd_relpath, b"subproject/subdir")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"subproject")

        with chdir("subproject-second"):
            superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()
            self.assertEqual(super_paths.super_to_cwd_relpath, b"subproject-second")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"subproject-second")
        with chdir("subproject-second/subdir"):
            superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject(enforce_cwd_is_subproject=False)
            self.assertEqual(super_paths.super_to_cwd_relpath, b"subproject-second/subdir")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"subproject-second")


class TestGenSubPaths(TestCaseTempFolder):
    def test_gen_sub_paths_from_relpath(self):
        super_abspath = os.getcwdb()
        super_paths = gen_super_paths(super_abspath)

        sub_paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
        self.assertEqual(sub_paths.super_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(sub_paths.cwd_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(sub_paths.sub_name, b"sub2")

        with create_and_chdir("sub1"):
            super_paths = gen_super_paths(super_abspath)
            sub_paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(sub_paths.cwd_to_sub_relpath, b"sub2")
            self.assertEqual(sub_paths.sub_name, b"sub2")

        with create_and_chdir("sub1/sub2"):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")
            self.assertEqual(paths.sub_name, b"sub2")

        with create_and_chdir("sub1/sub2/sub3"):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")
            self.assertEqual(paths.sub_name, b"sub2")

        with create_and_chdir("sub1/sub2/sub3/sub4"):
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

        with create_and_chdir("sub1"):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"sub2")
            self.assertEqual(paths.sub_name, b"sub2")

        with create_and_chdir("sub1/sub2"):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")
            self.assertEqual(paths.sub_name, b"sub2")

        with create_and_chdir("sub1/sub2/sub3"):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"..")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")
            self.assertEqual(paths.sub_name, b"sub2")

        with create_and_chdir("sub1/sub2/sub3/sub4"):
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

        with create_and_chdir("sub1/sub2/"):
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"..")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")

            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"../.")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")

            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b".")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")


if __name__ == '__main__':
    unittest.main()
