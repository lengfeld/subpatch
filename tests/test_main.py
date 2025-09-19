#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from os.path import dirname, join, realpath

from helpers import (TestCaseHelper, TestCaseTempFolder, create_and_chdir,
                     touch)

path = realpath(__file__)
sys.path.append(join(dirname(path), "../src"))

from main import (config_add_subproject, gen_sub_paths_from_cwd_and_relpath,
                  gen_sub_paths_from_relpath, gen_super_paths, read_metadata,
                  Metadata)


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
