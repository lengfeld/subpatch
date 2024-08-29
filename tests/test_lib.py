#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, mkdir, touch, Git

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from subpatch import git_get_toplevel


class TestGit(TestCaseTempFolder):
    def testGitGetToplevelNotInGitFolder(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                self.assertIsNone(git_get_toplevel())

    def testGitGetToplevel(self):
        mkdir("subproject")
        with cwd("subproject"):
            git = Git()
            git.init()
            touch("hello", b"content")
            git.add("hello")
            git.commit("msg")

            cur_cwd = os.getcwd().encode("utf8")
            git_path = git_get_toplevel()
            self.assertEqual(git_path, cur_cwd)
            self.assertTrue(git_path.endswith(b"/subproject"))

            mkdir("test")

            with cwd("test"):
                # It's still the toplevel dir, not the subdir "test"
                git_path = git_get_toplevel()
                self.assertEqual(git_path, cur_cwd)
                self.assertTrue(git_path.endswith(b"/subproject"))


if __name__ == '__main__':
    unittest.main()
