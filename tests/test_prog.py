#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from time import sleep
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, touch, Git, TestCaseHelper
from localwebserver import LocalWebserver, FileRequestHandler


path = realpath(__file__)
SUBPATCH_PATH = join(dirname(path), "..", "subpatch")


class TestSubpatch(TestCaseTempFolder):
    def run_subpatch(self, args, stderr=None, stdout=None):
        if os.environ.get("DEBUG", "0") == "1":
            print("Running subpatch command: %s" % (args,), file=sys.stderr)

        p = Popen([SUBPATCH_PATH] + args, stdout=stdout, stderr=stderr)
        stdout_output, stderr_output = p.communicate()
        # TODO This overwrites a member variable!
        # TODO introduce result tuple/class
        # TODO dump stdout and sterr for debugging testscases via env variable.
        # TODO dump stdout and sterr for debugging testscases via env variable.
        if os.environ.get("DEBUG", "0") == "1":
            if stdout_output is not None:
                print("stdout:", stdout_output.decode("utf8"), file=sys.stderr)
            if stderr_output is not None:
                print("stderr:", stderr_output.decode("utf8"), file=sys.stderr)
        p.stdout = stdout_output
        p.stderr = stderr_output
        return p

    def run_subpatch_ok(self, args, stderr=None, stdout=None):
        p = self.run_subpatch(args, stderr=stderr, stdout=stdout)
        self.assertEqual(p.returncode, 0)
        return p


class TestNoCommands(TestCaseHelper, TestSubpatch):
    def test_start_without_args(self):
        p = self.run_subpatch([], stderr=DEVNULL)
        self.assertEqual(p.returncode, 2)

    def test_version(self):
        p = self.run_subpatch_ok(["--version"], stdout=PIPE)
        self.assertIn(b"subpatch version ", p.stdout)
        p = self.run_subpatch_ok(["-v"], stdout=PIPE)
        self.assertIn(b"subpatch version ", p.stdout)

    def test_info(self):
        p = self.run_subpatch_ok(["--info"], stdout=PIPE)
        self.assertEqual(b"""\
homepage:  https://subpatch.net
git repo:  https://github.com/lengfeld/subpatch
license:   GPL-2.0-or-later
""", p.stdout)

    def test_control_c(self):
        # NOTE Using "deepcopy" or "copy" for 'os.environ' does not work.  It
        # does not make a copy. The original _global_ instance is changed.
        # Rework the code to use 'dict(os.environ)'. This makes a realy copy!.
        env = dict(os.environ)
        env["HANG_FOR_TEST"] = "1"
        p = Popen([SUBPATCH_PATH, "-v"], stderr=PIPE, env=env)

        # This is racy, but we have to wait until the subpatch process
        # is actually started, runs and waits in the sleep function.
        # TODO make it non-racy!
        sleep(0.10)
        from signal import SIGINT
        p.send_signal(SIGINT)

        _, stderr = p.communicate()
        self.assertEqual(3, p.returncode)
        self.assertEqual(b"Interrupted!\n", stderr)


def create_super_and_subproject():
    with cwd("subproject", create=True):
        git = Git()
        git.init()
        touch("hello", b"content")
        git.add("hello")
        git.commit("msg")

    with cwd("superproject", create=True):
        git = Git()
        git.init()
        touch("hello", b"content")
        git.add("hello")
        git.commit("msg")


class TestCmdStatus(TestCaseHelper, TestSubpatch):
    def test_not_in_superproject(self):
        # NOTE this does not fail, because the tmp folder is in the git folder
        # of the subpatch project itself.
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                p = self.run_subpatch(["status"], stderr=PIPE)
                self.assertEqual(p.returncode, 4)
                self.assertEqual(b"Error: No git repo as superproject found!\n",
                                 p.stderr)

    def test_no_subpatch_config_file(self):
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["status"], stderr=PIPE)
            self.assertEqual(b"Error: subpatch not yet configured for superproject!\n",
                             p.stderr)
            self.assertEqual(p.returncode, 4)

    def test_no_subpatch_config_file(self):
        create_super_and_subproject()
        with cwd("superproject"):
            self.run_subpatch_ok(["add", "../subproject"], stdout=DEVNULL)

            p = self.run_subpatch(["status"], stdout=PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(b"""\
NOTE: Output format is just a hack. Not the final output format yet!
[subpatch "subproject"]
\turl = ../subproject
""",
                             p.stdout)


class TestCmdAdd(TestCaseHelper, TestSubpatch):
    def test_not_in_superproject(self):
        # NOTE this does not fail, because the tmp folder is in the git folder
        # of the subpatch project itself.
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                p = self.run_subpatch(["add", "../ignore"], stderr=PIPE)
                self.assertEqual(b"Error: No git repo as superproject found!\n",
                                 p.stderr)
                self.assertEqual(p.returncode, 4)

    def test_without_url_arg(self):
        p = self.run_subpatch(["add"], stderr=PIPE)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"the following arguments are required: url", p.stderr)

    def test_subpatch_config_already_exists(self):
        create_super_and_subproject()

        with cwd("superproject"):
            touch(".subpatch", b"")

            p = self.run_subpatch(["add", "../subproject"], stderr=PIPE)
            self.assertEqual(b"Error: Feature not implemented yet!\n", p.stderr)
            self.assertEqual(4, p.returncode)

    def test_subproject_directory_already_exists(self):
        create_super_and_subproject()

        with cwd("superproject"):
            # Just create a file. It should also fail!
            touch("subproject", b"")

            p = self.run_subpatch(["add", "../subproject"], stderr=PIPE)
            self.assertEqual(b"Directory 'subproject' alreay exists. Cannot add subproject!\n", p.stderr)
            self.assertEqual(4, p.returncode)

    def test_add_with_trailing_slash(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            p = self.run_subpatch_ok(["add", "../subproject/"], stdout=PIPE)
            self.assertIn(b"Adding subproject 'subproject' was successful", p.stdout)
            self.assertTrue(os.path.isdir("subproject"))

            # NOTE The trailing slash in the URL in the config file!
            self.assertFileContent(".subpatch",
                                   b"[subpatch \"subproject\"]\n\turl = ../subproject/\n")

    def test_add_in_subdirectory(self):
        create_super_and_subproject()

        # Prepare repo for dump http protocol
        # See https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
        with cwd("subproject"):
            git = Git()
            git.call(["update-server-info"])

        with LocalWebserver(8000, FileRequestHandler), cwd("superproject"):
            git = Git()
            with cwd("subdir", create=True):
                p = self.run_subpatch_ok(["add", "http://localhost:8000/subproject/.git/"], stdout=PIPE)
                self.assertIn(b"Adding subproject 'subproject' was successful", p.stdout)
                self.assertTrue(os.path.isdir("subproject"))

            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubdir/subproject/hello"])

            self.assertFileContent(".subpatch",
                                   b"""\
[subpatch \"subdir/subproject\"]
\turl = http://localhost:8000/subproject/.git/
""")

    def test_add_with_stdout_output_and_index_updates(self):
        create_super_and_subproject()

        with cwd("superproject"):
            git = Git()
            p = self.run_subpatch_ok(["add", "../subproject"], stdout=PIPE)
            stdout = p.stdout
            self.assertEqual(b"""\
Adding subproject 'subproject' was successful.
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute 'git reset --merge`.
""",
                             stdout)

            # Check working tree
            self.assertFileExistsAndIsDir("subproject")

            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubproject/hello"])

            self.assertFileContent(".subpatch",
                                   b"[subpatch \"subproject\"]\n\turl = ../subproject\n")

    def test_add_with_extra_path_but_empty(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            p = self.run_subpatch(["add", "../subproject", ""], stdout=DEVNULL, stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid arguments: path is empty\n",
                             p.stderr)

    def test_add_with_extra_path(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()

            # TODO add "-q" argument
            p = self.run_subpatch_ok(["add", "../subproject", "folder"], stdout=DEVNULL)
            self.assertFileExistsAndIsDir("folder")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tfolder/hello"])
            self.assertFileContent(".subpatch",
                                   b"[subpatch \"folder\"]\n\turl = ../subproject\n")
            # Remove all stagged changes
            git.call(["reset", "--merge"])

            # Add same subproject but in a subfolder
            p = self.run_subpatch_ok(["add", "../subproject", "sub/folder"], stdout=DEVNULL)
            self.assertFileExistsAndIsDir("sub/folder")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsub/folder/hello"])
            self.assertFileContent(".subpatch",
                                   b"[subpatch \"sub/folder\"]\n\turl = ../subproject\n")

            # Remove all stagged changes
            git.call(["reset", "--merge"])

            # Add subproject with trailing slash in path
            p = self.run_subpatch_ok(["add", "../subproject", "folder/"], stdout=DEVNULL)

            self.assertFileExistsAndIsDir("folder")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tfolder/hello"])
            # NOTE: The trailing slash is removed
            self.assertFileContent(".subpatch",
                                   b"[subpatch \"folder\"]\n\turl = ../subproject\n")
            # Remove all stagged changes
            git.call(["reset", "--merge"])

    def test_add_in_subdirectory_with_relative_path_fails(self):
        create_super_and_subproject()
        with cwd("superproject/sub", create=True):
            p = self.run_subpatch(["add", "../../subproject"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: When using relative repository URLs, you current work diretory must be the toplevel folder of the superproject!\n",
                             p.stderr)


if __name__ == '__main__':
    unittest.main()
