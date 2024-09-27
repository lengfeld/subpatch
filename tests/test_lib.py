#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, touch, Git

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from subpatch import git_get_toplevel, git_get_object_type, get_url_type, \
                     URLTypes, get_name_from_repository_url


class TestGit(TestCaseTempFolder):
    def test_git_get_object_type(self):
        git = Git()
        git.init()
        touch("file", b"content")
        git.add("file")
        git.commit("message")
        git.tag("v1", "msg")

        self.assertEqual(b"commit", git_get_object_type(b"HEAD"))
        self.assertEqual(b"tree", git_get_object_type(b"HEAD^{tree}"))
        self.assertEqual(b"blob", git_get_object_type(b"HEAD:file"))
        self.assertEqual(b"tag", git_get_object_type(b"v1"))
        # TODO Catching the generic 'Exception' is bad. The code should use a
        # custom execption!
        self.assertRaises(Exception, git_get_object_type, b"vdoes-not-exists")

    def test_git_get_toplevel_not_in_git_folder(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                self.assertIsNone(git_get_toplevel())

    def test_git_get_toplevel(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()
            touch("hello", b"content")
            git.add("hello")
            git.commit("msg")

            cur_cwd = os.getcwd().encode("utf8")
            git_path = git_get_toplevel()
            self.assertEqual(git_path, cur_cwd)
            self.assertTrue(git_path.endswith(b"/subproject"))

            with cwd("test", create=True):
                # It's still the toplevel dir, not the subdir "test"
                git_path = git_get_toplevel()
                self.assertEqual(git_path, cur_cwd)
                self.assertTrue(git_path.endswith(b"/subproject"))


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

    def test_get_name_from_repository_url(self):
        f = get_name_from_repository_url
        self.assertEqual("name", f("name"))
        self.assertEqual("name", f("/name/"))
        self.assertEqual("name", f("/name/.git/"))
        self.assertEqual("name", f("/name/.git"))
        self.assertEqual("name", f("/name.git"))
        self.assertEqual("name", f("/name.git/"))
        self.assertEqual("name", f("sub/name.git/"))
        self.assertEqual("name", f("http://localhost:8000/name/.git/"))


if __name__ == '__main__':
    unittest.main()
