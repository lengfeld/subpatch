#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from copy import copy
from time import sleep
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, mkdir, touch, Git


path = realpath(__file__)
SUBPATCH_PATH = join(dirname(path), "..", "subpatch")


def subpatch(args, stderr=None, stdout=None):
    p = Popen([SUBPATCH_PATH] + args, stdout=stdout, stderr=stderr)
    stdout_output, stderr_output = p.communicate()
    # TODO This overwrites a member variable!
    # TODO introduce result tuple/class
    # TODO dump stdout and sterr for debugging testscases via env variable.
    # TODO dump stdout and sterr for debugging testscases via env variable.
    if os.environ.get("DEBUG", "0") == "1":
        if stdout_output is not None:
            print(stdout_output.decode("utf8"))
        if stderr_output is not None:
            print(stderr_output.decode("utf8"))
    p.stdout = stdout_output
    p.stderr = stderr_output
    return p


# TODO refactor to subclass. Otherwise 'self' is missleading.
def subpatchOk(self, args, stderr=None, stdout=None):
    p = subpatch(args, stderr=stderr, stdout=stdout)
    self.assertEqual(p.returncode, 0)
    return p


class MyTests(TestCaseTempFolder):
    def assertFileContent(self, filename, content):
        with open(filename, "br") as f:
            self.assertEqual(f.read(), content)


class TestNoCommands(MyTests):
    def testStartWithoutArgs(self):
        p = subpatch([], stderr=DEVNULL)
        self.assertEqual(p.returncode, 2)

    def testVersion(self):
        p = subpatchOk(self, ["--version"], stdout=PIPE)
        self.assertIn(b"subpatch version ", p.stdout)
        p = subpatchOk(self, ["-v"], stdout=PIPE)
        self.assertIn(b"subpatch version ", p.stdout)

    def testInfo(self):
        p = subpatchOk(self, ["--info"], stdout=PIPE)
        self.assertEqual(b"""\
homepage:  https://subpatch.net
git repo:  https://github.com/lengfeld/subpatch
license:   GPL-2.0-or-later
""", p.stdout)

    def test_control_c(self):
        env = copy(os.environ)
        env["HANG_FOR_TEST"] = "1"
        p = Popen([SUBPATCH_PATH, "-v"], stderr=PIPE, env=env)
        # This is racy, but we have to wait until the subpatch process
        # is actually started, runs and waits in the sleep function.
        # TODO make it non-racy!
        sleep(0.05)
        from signal import SIGINT
        p.send_signal(SIGINT)

        _, stderr = p.communicate()
        self.assertEqual(3, p.returncode)
        self.assertEqual(b"Interrupted!\n", stderr)


def create_super_and_subproject():
    mkdir("subproject")
    with cwd("subproject"):
        git = Git()
        git.init()
        touch("hello", b"content")
        git.add("hello")
        git.commit("msg")

    mkdir("superproject")
    with cwd("superproject"):
        git = Git()
        git.init()
        touch("hello", b"content")
        git.add("hello")
        git.commit("msg")


class TestCmdStatus(MyTests):
    def testNotInSuperproject(self):
        # NOTE this does not fail, because the tmp folder is in the git folder
        # of the subpatch project itself.
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                p = subpatch(["status"], stderr=PIPE)
                self.assertEqual(p.returncode, 4)
                self.assertEqual(b"Error: No git repo as superproject found!\n",
                                 p.stderr)

    def testNoSubpatchConfigFile(self):
        mkdir("superproject")
        with cwd("superproject"):
            git = Git()
            git.init()
            p = subpatch(["status"], stderr=PIPE)
            self.assertEqual(b"Error: subpatch not yet configured for superproject!\n",
                             p.stderr)
            self.assertEqual(p.returncode, 4)

    def testNoSubpatchConfigFile(self):
        create_super_and_subproject()
        with cwd("superproject"):
            subpatchOk(self, ["add", "../subproject"], stdout=DEVNULL)

            p = subpatch(["status"], stdout=PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(b"""\
NOTE: Output format is just a hack. Not the final output format yet!
[subpatch "subproject"]
\turl = ../subproject
""",
                             p.stdout)


class TestCmdAdd(MyTests):
    def test_not_in_superproject(self):
        # NOTE this does not fail, because the tmp folder is in the git folder
        # of the subpatch project itself.
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                p = subpatch(["add", "../ignore"], stderr=PIPE)
                self.assertEqual(b"Error: No git repo as superproject found!\n",
                                 p.stderr)
                self.assertEqual(p.returncode, 4)

    def test_without_url_arg(self):
        p = subpatch(["add"], stderr=PIPE)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"the following arguments are required: url", p.stderr)

    def test_subpatch_config_already_exists(self):
        create_super_and_subproject()

        with cwd("superproject"):
            touch(".subpatch", b"")

            p = subpatch(["add", "../subproject"], stderr=PIPE)
            self.assertEqual(b"Error: Feature not implemented yet!\n", p.stderr)
            self.assertEqual(4, p.returncode)

    def test_subproject_directory_already_exists(self):
        create_super_and_subproject()

        with cwd("superproject"):
            # Just create a file. It should also fail!
            touch("subproject", b"")

            p = subpatch(["add", "../subproject"], stderr=PIPE)
            self.assertEqual(b"Directory 'subproject' alreay exists. Cannot add subproject!\n", p.stderr)
            self.assertEqual(4, p.returncode)

    def test_add_with_trailing_slash(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            p = subpatchOk(self, ["add", "../subproject/"], stdout=PIPE)
            self.assertIn(b"Adding subproject 'subproject' was successful", p.stdout)
            self.assertTrue(os.path.isdir("subproject"))

            # NOTE The trailing slash in the url!
            self.assertFileContent(".subpatch",
                                   b"[subpatch \"subproject\"]\n\turl = ../subproject/\n")

    def test_add_in_subdirectory(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            mkdir("subdir")
            with cwd("subdir"):
                p = subpatchOk(self, ["add", "../../subproject"], stdout=PIPE)
                self.assertIn(b"Adding subproject 'subproject' was successful", p.stdout)
                self.assertTrue(os.path.isdir("subproject"))

            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubdir/subproject/hello"])

            self.assertFileContent(".subpatch",
                                   b"[subpatch \"subdir/subproject\"]\n\turl = ../../subproject\n")

    def test_add_with_stdout_output_and_index_updates(self):
        create_super_and_subproject()

        with cwd("superproject"):
            git = Git()
            p = subpatchOk(self, ["add", "../subproject"], stdout=PIPE)
            stdout = p.stdout
            self.assertEqual(b"""\
Adding subproject 'subproject' was successful.
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute 'git reset --merge`.
""",
                             stdout)

            # Check working tree
            self.assertTrue(os.path.isdir("subproject"))

            # TODO what is the coding style for member naming
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubproject/hello"])

            self.assertFileContent(".subpatch",
                                   b"[subpatch \"subproject\"]\n\turl = ../subproject\n")


if __name__ == '__main__':
    unittest.main()
