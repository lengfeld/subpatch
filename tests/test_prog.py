#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from copy import deepcopy
from os.path import dirname, join, realpath
from subprocess import DEVNULL, PIPE, Popen, run
from time import sleep

from helpers import (Git, TestCaseHelper, TestCaseTempFolder,
                     create_git_repo_with_branches_and_tags, cwd, touch)
from localwebserver import FileRequestHandler, LocalWebserver

path = realpath(__file__)
SUBPATCH_PATH = join(dirname(path), "..", "subpatch")

# TODO This is ugly. The test for the command line tool "subpatch" should not
# need to include Subpatch itself. The git tooling should be moved into a
# seperated file.
sys.path.append(join(dirname(path), "../"))
from subpatch import ObjectType, git_get_object_type, git_ls_files_untracked


class TestSubpatch:
    def run_subpatch(self, args, stderr=None, stdout=None, hack=False):
        if os.environ.get("DEBUG", "0") == "1":
            print("Running subpatch command: %s" % (args,), file=sys.stderr)

        # TODO This hack is so bad. Variable/function names are bad and not
        # nicly implemented
        env = deepcopy(os.environ)
        if hack:
            env["HACK_DISABLE_DEPTH_OPTIMIZATION"] = "1"
        p = Popen([SUBPATCH_PATH] + args, stdout=stdout, stderr=stderr, env=env)
        stdout_output, stderr_output = p.communicate()
        # TODO This overwrites a member variable!
        # TODO introduce result tuple/class
        if os.environ.get("DEBUG", "0") == "1":
            if stdout_output is not None:
                sys.stdout.flush()
                print("stdout:", stdout_output.decode("utf8"), file=sys.stderr)
                sys.stderr.flush()
            if stderr_output is not None:
                sys.stdout.flush()
                print("stderr:", stderr_output.decode("utf8"), file=sys.stderr)
                sys.stderr.flush()
        p.stdout = stdout_output
        p.stderr = stderr_output
        return p

    def run_subpatch_ok(self, args, stderr=None, stdout=None):
        p = self.run_subpatch(args, stderr=stderr, stdout=stdout)
        self.assertEqual(p.returncode, 0)
        return p


class TestNoCommands(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
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
license:   GPL-2.0-only
""", p.stdout)

    def test_control_c(self):
        signal_file_path = "/tmp/x"
        try:
            os.remove(signal_file_path)
        except FileNotFoundError:
            pass
        # NOTE Using "deepcopy" or "copy" for 'os.environ' does not work.  It
        # does not make a copy. The original _global_ instance is changed.
        # Rework the code to use 'dict(os.environ)'. This makes a realy copy!.
        env = dict(os.environ)
        env["HANG_FOR_TEST"] = signal_file_path
        p = Popen([SUBPATCH_PATH, "-v"], stderr=PIPE, env=env)

        # Very simple/handmade signalig from subpatch back to the test code.
        while True:
            if os.path.exists(signal_file_path):
                break
            sleep(0.10)
        from signal import SIGINT
        p.send_signal(SIGINT)
        os.remove(signal_file_path)

        _, stderr = p.communicate()
        self.assertEqual(b"Interrupted!\n", stderr)
        self.assertEqual(3, p.returncode)


class TestHelp(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_help(self):
        p = self.run_subpatch_ok(["help"], stdout=PIPE)
        self.assertTrue(p.stdout.startswith(b"usage: subpatch"))
        # TODO compare the outout with "--help". Should be the same.


def create_super_and_subproject():
    with cwd("subproject", create=True):
        git = Git()
        git.init()
        git.call(["switch", "-c", "main", "-q"])
        touch("hello", b"content")
        git.add("hello")
        git.commit("msg")
        git.tag("vtag", "some tag")
        # TODO check git commit id

    with cwd("superproject", create=True):
        git = Git()
        git.init()
        touch("hello", b"content")
        git.add("hello")
        git.commit("msg")
        # TODO check git commit id


# TODO update name. Also pop and push are tested!
class TestCmdApply(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def create_super_and_subproject_for_class(self):
        create_super_and_subproject()
        with cwd("subproject"):
            git = Git()
            touch("hello", b"new-content")
            git.add("hello")
            git.commit("changing hello")
            touch("hello", b"new-new-content")
            git.add("hello")
            git.commit("changing hello")
            git.call(["format-patch", "-q", "HEAD^^.."])
            git.call(["reset", "--hard", "HEAD^^", "-q"])
            self.assertFileExists("0001-changing-hello.patch")
            self.assertFileExists("0002-changing-hello.patch")

        with cwd("superproject"):
            git = Git()
            self.run_subpatch_ok(["add", "-q", "../subproject"])
            self.assertFileContent("subproject/hello", b"content")
            git.commit("add subproject")

    def test_cwd_errors(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject"):
            touch("test.patch")

            p = self.run_subpatch(["apply", "test.patch"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr,
                             b"Error: Invalid argument: Current work directory must be inside a subproject!\n")

            with cwd("subproject/subdir", create=True):
                p = self.run_subpatch(["apply", "../../test.patch"], stderr=PIPE)
                self.assertEqual(p.returncode, 4)
                self.assertEqual(p.stderr,
                                 b"Error: Invalid argument: Current work directory must be the toplevel directory of the subproject for now!\n")

    def test_apply_simple_case(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject"):
            git = Git()
            self.assertFileContent("subproject/hello", b"content")

            with cwd("subproject"):
                p = self.run_subpatch_ok(["apply", "../../subproject/0001-changing-hello.patch"], stdout=PIPE)
            self.assertFileContent("subproject/hello", b"new-content")
            self.assertFileExists("subproject/patches/0001-changing-hello.patch")
            self.assertEqual(git.diff_staged_files(),
                             [b"M\tsubproject/hello",
                              b'A\tsubproject/patches/0001-changing-hello.patch'])
            self.assertEqual(p.stdout, b"""\
Applied patch '../../subproject/0001-changing-hello.patch' to subproject 'subproject' successfully!
The following changes are recorded in the git index:
 2 files changed, 22 insertions(+), 1 deletion(-)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")

    def test_multiple_patches(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject/subproject"):
            self.run_subpatch_ok(["apply", "-q", "../../subproject/0001-changing-hello.patch"])
            self.assertFileContent("hello", b"new-content")
            self.assertFileExists("patches/0001-changing-hello.patch")
            self.assertFileDoesNotExist("patches/0002-changing-hello.patch")

            self.run_subpatch_ok(["apply", "-q", "../../subproject/0002-changing-hello.patch"])
            self.assertFileContent("hello", b"new-new-content")
            self.assertFileExists("patches/0001-changing-hello.patch")
            self.assertFileExists("patches/0002-changing-hello.patch")

            # Now pop two patches
            self.run_subpatch_ok(["pop", "-q"])
            self.assertFileContent("hello", b"new-content")

            self.run_subpatch_ok(["pop", "-q"])
            self.assertFileContent("hello", b"content")

            # The patch files are still there
            self.assertFileExists("patches/0001-changing-hello.patch")
            self.assertFileExists("patches/0002-changing-hello.patch")

            # But it is recorded in the metadata
            self.assertFileContent(".subproject", b"""\
[patches]
\tappliedIndex = -1
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")

            # Now push again
            self.run_subpatch_ok(["push", "-q"])
            self.assertFileContent("hello", b"new-content")

            self.run_subpatch_ok(["push", "-q"])
            self.assertFileContent("hello", b"new-new-content")

    def test_push_pop_no_patches(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject/subproject"):
            p = self.run_subpatch(["pop"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr, b"Error: Invalid argument: There is no patch to pop!\n")

            p = self.run_subpatch(["push"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr, b"Error: Invalid argument: There is no patch to push!\n")

    def test_error_not_all_applied(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject/subproject"):
            self.run_subpatch_ok(["apply", "-q", "../../subproject/0001-changing-hello.patch"])
            self.run_subpatch_ok(["pop", "-q"])
            p = self.run_subpatch(["apply", "-q", "../../subproject/0002-changing-hello.patch"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr,
                             b"Error: Invalid argument: Cannot apply new patch. Not all existing patches are applied!\n")

    def test_error_patch_filename_not_correct(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject/subproject"):
            self.run_subpatch_ok(["apply", "-q", "../../subproject/0001-changing-hello.patch"])

            # First test that the patch filename is unique
            p = self.run_subpatch(["apply", "-q", "../../subproject/0001-changing-hello.patch"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr,
                             b"Error: Invalid argument: The filename '0001-changing-hello.patch' must be unique. There is already a patch with the same name!\n")

            # Second test that the patch filename is in order (=higher)
            # -> Rename the second patch file to provoke the error
            with cwd("../../subproject/"):
                os.rename("0002-changing-hello.patch", "0000-changing-hello.patch")
            p = self.run_subpatch(["apply", "-q", "../../subproject/0000-changing-hello.patch"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr,
                             b"Error: Invalid argument: The patch filenames must be in order. The new patch filename '0000-changing-hello.patch' does not sort latest!\n")

    def test_pop_push_simple_case(self):
        self.create_super_and_subproject_for_class()
        with cwd("superproject"):
            git = Git()
            with cwd("subproject"):
                self.run_subpatch_ok(["apply", "-q", "../../subproject/0001-changing-hello.patch"], stdout=PIPE)
            self.assertEqual(git.diff_staged_files(),
                             [b"M\tsubproject/hello",
                              b'A\tsubproject/patches/0001-changing-hello.patch'])
            self.assertFileContent("subproject/hello", b"new-content")

            with cwd("subproject"):
                p = self.run_subpatch_ok(["pop"], stdout=PIPE)
            self.assertEqual(git.diff_staged_files(),
                             [b"M\tsubproject/.subproject",
                              b'A\tsubproject/patches/0001-changing-hello.patch'])
            self.assertFileContent("subproject/hello", b"content")
            self.assertFileContent("subproject/.subproject", b"""\
[patches]
\tappliedIndex = -1
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")
            self.assertEqual(p.stdout, b"""\
Poped patch '0001-changing-hello.patch' from subproject 'subproject' successfully!
The following changes are recorded in the git index:
 2 files changed, 23 insertions(+)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")

            with cwd("subproject"):
                p = self.run_subpatch_ok(["push"], stdout=PIPE)
            self.assertEqual(git.diff_staged_files(),
                             [b"M\tsubproject/hello",
                              b'A\tsubproject/patches/0001-changing-hello.patch'])
            self.assertFileContent("subproject/hello", b"new-content")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")
            self.assertEqual(p.stdout, b"""\
Pushed patch '0001-changing-hello.patch' to subproject 'subproject' successfully!
The following changes are recorded in the git index:
 2 files changed, 22 insertions(+), 1 deletion(-)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")

    def test_status(self):
        self.create_super_and_subproject_for_class()

        with cwd("superproject"):
            git = Git()
            with cwd("subproject"):
                self.run_subpatch_ok(["apply", "-q", "../../subproject/0001-changing-hello.patch"])
                self.run_subpatch_ok(["apply", "-q", "../../subproject/0002-changing-hello.patch"])
                self.run_subpatch_ok(["pop", "-q"])
                git.commit("add patches")

            p = self.run_subpatch_ok(["status"], stdout=PIPE)
            self.assertEqual(b"""\
NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
NOTE: The format is markdown currently. Will mostly change in the future.

# subproject at 'subproject'

* was integrated from URL: ../subproject
* has integrated object id: c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
* There are n=2 patches.
* There are only n=1 patches applied.
""", p.stdout)


class TestCmdList(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_no_subpatch_config_file(self):
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["list"], stderr=PIPE)
            self.assertEqual(b"Error: subpatch not yet configured for superproject!\n",
                             p.stderr)
            self.assertEqual(p.returncode, 4)

    def test_one_and_two_subproject(self):
        create_super_and_subproject()
        with cwd("superproject"):
            self.run_subpatch_ok(["add", "-q", "../subproject", "first"])

            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(b"first\n", p.stdout)

            self.run_subpatch_ok(["add", "-q", "../subproject", "external/second"])

            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(b"external/second\nfirst\n", p.stdout)

    def test_order_is_the_same_as_in_config(self):
        git = Git()
        git.init()
        touch(".subpatch", b"""\
[subprojects]
path = c_not
path = b_in
path = a_alphabetical_order
""")

        # TODO add command to check that this handmade config is valid!

        p = self.run_subpatch_ok(["list"], stdout=PIPE)
        self.assertEqual(b"c_not\nb_in\na_alphabetical_order\n", p.stdout)


class TestCmdStatus(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_no_subpatch_config_file(self):
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["status"], stderr=PIPE)
            self.assertEqual(b"Error: subpatch not yet configured for superproject!\n",
                             p.stderr)
            self.assertEqual(p.returncode, 4)

    def test_two_clean_subprojects(self):
        create_super_and_subproject()
        with cwd("superproject"):
            self.run_subpatch_ok(["add", "-q", "../subproject", "subproject1"])
            self.run_subpatch_ok(["add", "-q", "../subproject", "subproject2"])
            git = Git()
            git.commit("add two subprojects")

            p = self.run_subpatch_ok(["status"], stdout=PIPE)
            self.assertEqual(b"""\
NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
NOTE: The format is markdown currently. Will mostly change in the future.

# subproject at 'subproject1'

* was integrated from URL: ../subproject
* has integrated object id: c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c

# subproject at 'subproject2'

* was integrated from URL: ../subproject
* has integrated object id: c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
""",
                             p.stdout)

            with cwd("subproject1"):
                p = self.run_subpatch_ok(["status"], stdout=PIPE)
                self.assertEqual(b"""\
NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
NOTE: The format is markdown currently. Will mostly change in the future.
WARNING: The current working directory is not the toplevel directory of the superproject.
WARNING: The paths in this console output are wrong (for now)!

# subproject at 'subproject1'

* was integrated from URL: ../subproject
* has integrated object id: c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c

# subproject at 'subproject2'

* was integrated from URL: ../subproject
* has integrated object id: c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
""",
                             p.stdout)

    def test_one_subproject_with_modified_files(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()
            touch("a")
            touch("b")
            touch("c")
            git.add("a")
            git.add("b")
            git.add("c")
            git.commit("stuff")

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            self.run_subpatch_ok(["add", "-q", "../subproject"])
            git.commit("add subproject")

            with cwd("subproject"):
                touch("a", b"x")
                touch("b", b"x")
                touch("c", b"x")
                git.add("a")
                # So files 'b' and 'c' are modified, but not staged
                # And file "a" is odified and staged

                touch("untracked")

            p = self.run_subpatch_ok(["status"], stdout=PIPE)
            self.assertEqual(b"""\
NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
NOTE: The format is markdown currently. Will mostly change in the future.

# subproject at 'subproject'

* was integrated from URL: ../subproject
* has integrated object id: a094853f138e0f388d787aca36354e1c3e7d1a2a
* There are n=1 untracked files and/or directories:
    - To see them execute:
        `git status subproject`
        `git ls-files --exclude-standard -o subproject`
    - Use `git add subproject` to add all of them
    - Use `git add subproject/<filename>` to just add some of them
    - Use `rm <filename>` to remove them
* There are n=2 modified files not staged for commit:
    - To see them execute:
        `git status subproject` or
        `git diff subproject`
    - Use `git add subproject` to update what will be committed
    - Use `git restore subproject` to discard changes in working directory
* There are n=1 modified files that are staged, but not committed:
    - To see them execute:
        `git status subproject` or
        `git diff --staged subproject`
    - Use `git commit subproject` to commit the changes
    - Use `git restore --staged subproject` to unstage
""",
                             p.stdout)


class TestCmdAdd(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_not_in_superproject(self):
        p = self.run_subpatch(["add", "../ignore"], stderr=PIPE)
        self.assertEqual(b"Error: No superproject found!\n", p.stderr)
        self.assertEqual(p.returncode, 4)

    def test_without_url_arg(self):
        p = self.run_subpatch(["add"], stderr=PIPE)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"the following arguments are required: url", p.stderr)

    def test_adding_two_subprojects(self):
        create_super_and_subproject()

        with cwd("superproject"):
            p = self.run_subpatch(["add", "-q", "../subproject", "dirB"])
            self.assertEqual(0, p.returncode)
            p = self.run_subpatch(["add", "-q", "../subproject", "dirA"])
            self.assertEqual(0, p.returncode)

            git = Git()
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tdirA/.subproject",
                              b"A\tdirA/hello",
                              b"A\tdirB/.subproject",
                              b"A\tdirB/hello"])

            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = dirA
\tpath = dirB
""")
            self.assertFileContent("dirA/.subproject", b"""\
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")
            self.assertFileContent("dirB/.subproject", b"""\
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")

    def test_gitignore_in_subproject(self):
        # Testing for a bug. There was a "-f" missing for "git add".
        with cwd("subproject", create=True):
            git = Git()
            git.init()
            touch("a")
            touch(".gitignore", b"a\n")
            git.add(".gitignore")
            git.call(["add", "-f", "a"])
            git.commit("first commit")

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            self.run_subpatch_ok(["add", "-q", "../subproject"])
            self.assertFileContent("subproject/a", b"")
            self.assertFileContent("subproject/.gitignore", b"a\n")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubproject/.gitignore",
                              b"A\tsubproject/.subproject",
                              b"A\tsubproject/a"])

    def test_subproject_directory_already_exists(self):
        create_super_and_subproject()

        with cwd("superproject"):
            # Just create a file. It should also fail!
            touch("subproject")

            p = self.run_subpatch(["add", "../subproject"], stderr=PIPE)
            self.assertEqual(b"Error: Directory 'subproject' alreay exists. Cannot add subproject!\n", p.stderr)
            self.assertEqual(4, p.returncode)

    def test_add_in_subdirectory(self):
        create_super_and_subproject()

        # Prepare repo for dump http protocol
        # See https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
        with cwd("subproject"):
            git = Git()
            git.call(["update-server-info"])

        with LocalWebserver(7000, FileRequestHandler), cwd("superproject"):
            git = Git()
            with cwd("subdir", create=True):
                # NOTE: This also tests that "/.git/" is not used as the local
                # directory name.
                p = self.run_subpatch_ok(["add", "http://localhost:7000/subproject/.git/"], stdout=PIPE)
                self.assertIn(b"Adding subproject 'subproject' from URL 'http://localhost:7000/subproject/.git/' at revision 'HEAD'... Done",
                              p.stdout)
                self.assertTrue(os.path.isdir("subproject"))

            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubdir/subproject/.subproject",
                              b"A\tsubdir/subproject/hello"])

            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = subdir/subproject
""")

    def test_add_with_stdout_output_and_index_updates(self):
        create_super_and_subproject()

        with cwd("superproject"):
            git = Git()
            p = self.run_subpatch_ok(["add", "../subproject"], stdout=PIPE)
            self.assertEqual(b"""\
Adding subproject 'subproject' from URL '../subproject' at revision 'HEAD'... Done.
The following changes are recorded in the git index:
 3 files changed, 6 insertions(+)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""", p.stdout)

            # Check working tree
            self.assertFileExistsAndIsDir("subproject")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubproject/.subproject",
                              b"A\tsubproject/hello"])
            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = subproject
""")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")

    def test_add_with_extra_path_but_empty(self):
        create_super_and_subproject()
        with cwd("superproject"):
            p = self.run_subpatch(["add", "../subproject", ""], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: path is empty\n",
                             p.stderr)

    def test_absolute_paths_are_not_supported(self):
        create_super_and_subproject()
        with cwd("superproject"):
            p = self.run_subpatch(["add", "/tmp/subproject"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Absolute local paths to a remote repository are not supported!\n",
                             p.stderr)

    def test_remote_git_repo_is_empty(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            p = self.run_subpatch(["add", "../subproject", "-r", "master"], stderr=PIPE, stdout=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Adding subproject 'subproject' from URL '../subproject' at revision 'master'... Failed.\n",
                             p.stdout)
            self.assertEqual(b"Error: Invalid argument: The reference 'master' cannot be resolved to a branch or tag!\n",
                             p.stderr)
            # TODO add test without "-r" argument. The internal code behaves differently!

    def test_add_with_extra_path(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()

            self.run_subpatch_ok(["add", "-q", "../subproject", "folder"])
            self.assertFileExistsAndIsDir("folder")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tfolder/.subproject",
                              b"A\tfolder/hello"])
            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = folder
""")
            git.remove_staged_changes()

            # Add same subproject but in a subfolder
            self.run_subpatch_ok(["add", "-q", "../subproject", "sub/folder"])
            self.assertFileExistsAndIsDir("sub/folder")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsub/folder/.subproject",
                              b"A\tsub/folder/hello"])
            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = sub/folder
""")
            git.remove_staged_changes()

            # Add subproject with trailing slash in path
            self.run_subpatch_ok(["add", "-q", "../subproject", "folder/"])

            self.assertFileExistsAndIsDir("folder")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tfolder/.subproject",
                              b"A\tfolder/hello"])
            # NOTE: The trailing slash is removed
            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = folder
""")
            git.remove_staged_changes()

    def test_add_in_subdirectory_with_relative_path_fails(self):
        create_super_and_subproject()
        with cwd("superproject/sub", create=True):
            p = self.run_subpatch(["add", "../../subproject"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: When using relative repository URLs, you current work directory must be the toplevel folder of the superproject!\n",
                             p.stderr)

    def test_with_invalid_revision(self):
        with cwd("subproject", create=True):
            create_git_repo_with_branches_and_tags()
            git = Git()
            object_id_file = git.get_sha1("main:file")
            self.assertEqual(ObjectType.BLOB, git_get_object_type(object_id_file))
            self.assertEqual(b"177324cdffb43c57471674a4655a2a513ab158f5", object_id_file)

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            p = self.run_subpatch(["add", "-q", "../subproject", "-r", "main-does-not-exists"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: The reference 'main-does-not-exists' cannot be resolved to a branch or tag!\n",
                             p.stderr)
            git.remove_staged_changes()  # NOTE: Revert changes subpatch already made!

            invalid_object_id = b"0" * 40
            p = self.run_subpatch(["add", "-q", "../subproject", "-r", invalid_object_id], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: Object id '0000000000000000000000000000000000000000' does not point to a valid object!\n",
                             p.stderr)
            git.remove_staged_changes()  # NOTE: Revert changes subpatch already made!

            p = self.run_subpatch(["add", "-q", "../subproject", "-r", object_id_file], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: Object id '177324cdffb43c57471674a4655a2a513ab158f5' does not point to a commit or tag object!\n",
                             p.stderr)
            git.remove_staged_changes()  # NOTE: Revert changes subpatch already made!

            p = self.run_subpatch(["add", "-q", "../subproject", "-r", "refs/heads\nmain"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: revision 'refs/heads\nmain' is invalid\n",
                             p.stderr)
            git.remove_staged_changes()  # NOTE: Revert changes subpatch already made!

    def test_with_revision(self):
        with cwd("subproject", create=True):
            create_git_repo_with_branches_and_tags()
            git = Git()
            # Ensure that these objects have different types
            object_id_commit = git.get_sha1("v1-stable")
            self.assertEqual(object_id_commit, b"32c32dcaa3c7f7024387640a91e98a5201e1f202")
            self.assertEqual(ObjectType.COMMIT, git_get_object_type(object_id_commit))
            object_id_tag = git.get_sha1("v2")
            self.assertEqual(object_id_tag, b"60c7ec01d2a8d8c450896bb683c16637d52ea63c")
            self.assertEqual(ObjectType.TAG, git_get_object_type(object_id_tag))

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            p = self.run_subpatch_ok(["add", "../subproject", "-r", "refs/heads/main"], stdout=PIPE)
            # NOTE: Checking the stdout here for a single time. There was a bug
            # in git_reset_hard().
            self.assertEqual(b"""\
Adding subproject 'subproject' from URL '../subproject' at revision 'refs/heads/main'... Done.
The following changes are recorded in the git index:
 3 files changed, 7 insertions(+)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""",
                             p.stdout)
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"change on main")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = 449e289b617c25c95868658a580b6c52fb817f4d
\trevision = refs/heads/main
\turl = ../subproject
""")
            git.remove_staged_changes()

            p = self.run_subpatch_ok(["add", "-q", "../subproject", "-r", "v1"])
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"initial")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = 20650350f66b12d5c34194a90c5b0a6e2771e8a5
\trevision = v1
\turl = ../subproject
""")
            git.remove_staged_changes()

            p = self.run_subpatch_ok(["add", "-q", "../subproject", "-r", object_id_commit])
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"change on stable")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = 32c32dcaa3c7f7024387640a91e98a5201e1f202
\trevision = 32c32dcaa3c7f7024387640a91e98a5201e1f202
\turl = ../subproject
""")
            git.remove_staged_changes()

            p = self.run_subpatch_ok(["add", "-q", "../subproject", "-r", object_id_tag])
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"change on main")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = 60c7ec01d2a8d8c450896bb683c16637d52ea63c
\trevision = 60c7ec01d2a8d8c450896bb683c16637d52ea63c
\turl = ../subproject
""")
            git.remove_staged_changes()

            # Special case: Test revision argument with subdirectory for
            # subproject. This was broken.
            p = self.run_subpatch_ok(["add", "-q", "-r", "v1", "../subproject", "subdir/subproject"])
            self.assertFileExistsAndIsDir("subdir/subproject")
            self.assertFileContent("subdir/subproject/file", b"initial")
            self.assertFileContent("subdir/subproject/.subproject", b"""\
[upstream]
\tobjectId = 20650350f66b12d5c34194a90c5b0a6e2771e8a5
\trevision = v1
\turl = ../subproject
""")
            git.remove_staged_changes()


class TestCmdConfigure(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_subpatch_config_does_not_match_scm(self):
        git = Git()
        git.init()
        with cwd("sub", create=True):
            touch(".subpatch", b"")
            p = self.run_subpatch(["configure"], stderr=PIPE)
            self.assertEqual(p.returncode, 4)
            self.assertEqual(p.stderr,
                             b"Error: Feature not implemented yet: subpatch config file is not at the root of the SCM repository!\n")

    def test_configure_in_git(self):
        git = Git()
        git.init()
        self.assertFileExists(".git")
        self.assertFileDoesNotExist(".subpatch")
        self.assertEqual(git.diff_staged_files(), [])

        p = self.run_subpatch_ok(["configure"], stdout=PIPE)
        self.assertEqual(p.stdout, b"""\
The file .subpatch was created in the toplevel directory.
Now use 'git commit' to finalized your change.
""")
        self.assertFileContent(".subpatch", b"")
        self.assertEqual(git.diff_staged_files(), [b"A\t.subpatch"])

        git.remove_staged_changes()

        # Test in subdirectory
        with cwd(b"sub", create=True):
            self.run_subpatch_ok(["configure", "-q"])
            self.assertFileContent("../.subpatch", b"")
            self.assertEqual(git.diff_staged_files(), [b"A\t.subpatch"])

    def test_after_configure_list_and_add_are_possible(self):
        create_super_and_subproject()
        with cwd("superproject"):
            self.run_subpatch_ok(["configure", "-q"])

            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(p.stdout, b"")

            self.run_subpatch_ok(["add", "-q", "../subproject"])

            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(p.stdout, b"subproject\n")

    def test_not_in_git_not_yet_supported(self):
        p = self.run_subpatch(["configure"], stderr=PIPE)
        self.assertEqual(p.returncode, 4)
        self.assertEqual(p.stderr,
                         b"Error: Feature not implemented yet: No SCM found. Cannot configure. '--here' not implemented yet!\n")


class TestCmdUpdate(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_some_errors_cases(self):
        with cwd("subproject", create=True):
            create_git_repo_with_branches_and_tags()

        with cwd("superproject", create=True):
            git = Git()
            git.init()
            self.run_subpatch_ok(["add", "-q", "-r", "v1", "../subproject", "dir/subproject"])
            git.commit("add subproject")
            self.assertFileContent("dir/subproject/file", b"initial")

            p = self.run_subpatch(["update", "no_subproject_dir", "-r", "v2"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: Path 'no_subproject_dir' does not point to a subproject\n",
                             p.stderr)

            # Unstaged changes in subproject are an error
            touch("dir/subproject/file", b"changes")
            p = self.run_subpatch(["update", "dir/subproject", "-r", "v2"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: There are unstaged changes in the subproject.\n",
                             p.stderr)

            # Staged changes in subproject are an error
            git.add("dir/subproject/file")
            p = self.run_subpatch(["update", "dir/subproject", "-r", "v2"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: There are staged changes in the subproject.\n",
                             p.stderr)

            git.remove_staged_changes()

    def create_subproject(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()

            os.mkdir("dir")
            touch("dir/b", b"first\n")
            touch("dir/c", b"first\n")
            touch("dir/d", b"first\n")
            # NOTE: Also test a sub-sub-directory. There was a bug in the code.
            os.mkdir("dir/dir1")
            touch("dir/dir1/f", b"first\n")
            git.add(b"dir")

            # NOTE: Adding a gitignore file and ignore one of the files. This
            # was a bug in the code. A missing "-f" for "git add" was the
            # error.
            touch("a", b"first-toplevel\n")
            touch(".gitignore", b"a\n")
            git.call(["add", "-f", "a"])
            git.add(".gitignore")

            git.commit("initial commit")
            git.tag("v1", "v1")

            # First test: file content is changed
            touch("dir/b", b"second\n")
            # Second test: file mode is changed
            os.chmod("dir/c", 0o777)
            # Third test: file is removed
            os.remove("dir/d")
            # Fourth test: file is added
            touch("dir/e", b"second\n")
            git.add(b"dir")
            git.commit("second commit")
            git.tag("v2", "v2")

    def test_simple_update(self):
        self.create_subproject()

        with cwd("superproject", create=True):
            git = Git()
            git.init()
            self.run_subpatch_ok(["add", "-q", "-r", "v1", "../subproject", "dir/subproject"])
            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = dir/subproject
""")
            self.assertFileContent("dir/subproject/.subproject", b"""\
[upstream]
\tobjectId = 97d971584b8d9ef942abc6a88e500c5233fb89b3
\trevision = v1
\turl = ../subproject
""")
            self.assertFileExistsAndIsDir("dir/subproject/dir")
            self.assertFileContent("dir/subproject/a", b"first-toplevel\n")
            self.assertFileContent("dir/subproject/dir/b", b"first\n")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tdir/subproject/.gitignore",
                              b"A\tdir/subproject/.subproject",
                              b"A\tdir/subproject/a",
                              b"A\tdir/subproject/dir/b",
                              b"A\tdir/subproject/dir/c",
                              b"A\tdir/subproject/dir/d",
                              b"A\tdir/subproject/dir/dir1/f"])
            git.commit("add subproject")

            p = self.run_subpatch(["update", "dir/subproject", "-r", "v2"], stdout=DEVNULL)
            self.assertEqual(0, p.returncode)

            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = dir/subproject
""")
            self.assertFileContent("dir/subproject/.subproject", b"""\
[upstream]
\tobjectId = 05273055cdb7635593d13ad7ce4d6da309050ce9
\trevision = v2
\turl = ../subproject
""")
            self.assertEqual(git.diff_staged_files(),
                             [b"M\tdir/subproject/.subproject",
                              b"M\tdir/subproject/dir/b",
                              b"M\tdir/subproject/dir/c",
                              b"D\tdir/subproject/dir/d",
                              b"A\tdir/subproject/dir/e"])
            self.assertFileExistsAndIsDir("dir/subproject/dir")
            self.assertFileContent("dir/subproject/a", b"first-toplevel\n")
            self.assertFileContent("dir/subproject/dir/b", b"second\n")
            self.assertFileContent("dir/subproject/dir/c", b"first\n")
            self.assertFileContent("dir/subproject/dir/e", b"second\n")
            self.assertEqual(git.diff(staged=True), b"""\
diff --git a/dir/subproject/.subproject b/dir/subproject/.subproject
index 59c08af..dea6d51 100644
--- a/dir/subproject/.subproject
+++ b/dir/subproject/.subproject
@@ -1,4 +1,4 @@
 [upstream]
-\tobjectId = 97d971584b8d9ef942abc6a88e500c5233fb89b3
-\trevision = v1
+\tobjectId = 05273055cdb7635593d13ad7ce4d6da309050ce9
+\trevision = v2
 \turl = ../subproject
diff --git a/dir/subproject/dir/b b/dir/subproject/dir/b
index 9c59e24..e019be0 100644
--- a/dir/subproject/dir/b
+++ b/dir/subproject/dir/b
@@ -1 +1 @@
-first
+second
diff --git a/dir/subproject/dir/c b/dir/subproject/dir/c
old mode 100644
new mode 100755
diff --git a/dir/subproject/dir/d b/dir/subproject/dir/d
deleted file mode 100644
index 9c59e24..0000000
--- a/dir/subproject/dir/d
+++ /dev/null
@@ -1 +0,0 @@
-first
diff --git a/dir/subproject/dir/e b/dir/subproject/dir/e
new file mode 100644
index 0000000..e019be0
--- /dev/null
+++ b/dir/subproject/dir/e
@@ -0,0 +1 @@
+second
""")

    def test_update_with_untracked_files(self):
        self.create_subproject()
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["add", "-q", "-r", "v1", "../subproject", "subproject"])
            self.assertEqual(p.returncode, 0)
            git.commit("add subproject")

            # Testing that a non-tracked file in the subproject is not removed on the update
            # First: Create the file
            touch("subproject/dir/untracked-file", b"untracked file\n")
            self.assertEqual(git_ls_files_untracked(),
                             [b"subproject/dir/untracked-file"])

            p = self.run_subpatch(["update", "subproject", "-r", "v2"], stdout=PIPE)

            # Second: Checking that the untracked file is still untracked and
            # still there and not modified.
            self.assertEqual(git_ls_files_untracked(),
                             [b"subproject/dir/untracked-file"])
            self.assertFileContent("subproject/dir/untracked-file", b"untracked file\n")

    def test_stdout_of_add_and_update_are_the_simliar(self):
        self.create_subproject()
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["add", "-r", "v1", "../subproject", "subproject"], stdout=PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"""\
Adding subproject 'subproject' from URL '../subproject' at revision 'v1'... Done.
The following changes are recorded in the git index:
 8 files changed, 12 insertions(+)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")
            git.commit("adding subproject")

            p = self.run_subpatch_ok(["update", "subproject", "-r", "v2"], stdout=PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"""\
Updating subproject 'subproject' from URL '../subproject' to revision 'v2'... Done.
The following changes are recorded in the git index:
 5 files changed, 4 insertions(+), 4 deletions(-)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")

            # TODO also check relative path that is currently down below in the
            # test "test_update_with_cwd_in_subdir"

    def test_update_with_cwd_in_subdir(self):
        self.create_subproject()
        with cwd("subproject"):
            git = Git()
            git.call(["update-server-info"])

        with LocalWebserver(7000, FileRequestHandler), cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["add", "-q", "-r", "v1", "http://localhost:7000/subproject/.git/", "dir/subproject"], hack=True)
            self.assertEqual(p.returncode, 0)
            git.commit("add subproject")

            # Get reference diff
            p = self.run_subpatch(["update", "dir/subproject", "-r", "v2"], stdout=DEVNULL, hack=True)
            self.assertEqual(p.returncode, 0)

            diff_ok = git.diff(staged=True)
            git.remove_staged_changes()

            with cwd("dir"):
                p = self.run_subpatch(["update", "subproject", "-r", "v2"], stdout=PIPE, hack=True)
                self.assertEqual(p.returncode, 0)
                # NOTE: Path in output is relative to the current work directory!
                self.assertEqual(p.stdout, b"""\
Updating subproject 'subproject' from URL 'http://localhost:7000/subproject/.git/' to revision 'v2'... Done.
The following changes are recorded in the git index:
 5 files changed, 4 insertions(+), 4 deletions(-)
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")
                self.assertEqual(git.diff(staged=True), diff_ok)

    def test_update_with_head(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()
            touch("a")
            git.add("a")
            git.commit("adding a")

        with cwd("superproject", create=True):
            git = Git()
            git.init()
            self.run_subpatch_ok(["add", "-q", "../subproject"])
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = 78733648ec0177bf0bc0c6d681cc80c37d8749ff
\turl = ../subproject
""")
            git.commit("add subproject")

            # There are no changes in the subproject yet
            self.run_subpatch_ok(["update", "subproject"], stdout=PIPE)
            self.assertEqual(git.diff_staged_files(), [])

        with cwd("subproject"):
            git = Git()
            touch("b")
            git.add("b")
            git.commit("adding b")

        with cwd("superproject"):
            # Now there are changes in the subproject
            self.run_subpatch_ok(["update", "subproject"], stdout=PIPE)
            self.assertEqual(git.diff_staged_files(),
                             [b"M\tsubproject/.subproject", b"A\tsubproject/b"])

    def test_update_has_no_changes(self):
        self.create_subproject()
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            self.run_subpatch_ok(["add", "-q", "-r", "v1", "../subproject", "subproject"])
            git.commit("add subproject")

            p = self.run_subpatch_ok(["update", "-r", "v1", "subproject"], stdout=PIPE)
            self.assertEqual(p.stdout, b"""\
Updating subproject 'subproject' from URL '../subproject' to revision 'v1'... Done.
Note: There are no changes in the subproject. Nothing to commit!
""")


class TestNoGit(TestCaseHelper, TestSubpatch, TestCaseTempFolder):
    def test_git_archive_export(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            self.run_subpatch_ok(["add", "-q", "../subproject"])
            git.commit("add subproject")

            git.call(["archive", "-o", "archive.tar", "HEAD"])

            # check archiv:
            p = run(["tar", "tvf", "archive.tar"], stdout=PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"""\
-rw-rw-r-- root/root        33 2001-10-09 13:00 .subpatch
-rw-rw-r-- root/root         7 2001-10-09 13:00 hello
drwxrwxr-x root/root         0 2001-10-09 13:00 subproject/
-rw-rw-r-- root/root        85 2001-10-09 13:00 subproject/.subproject
-rw-rw-r-- root/root         7 2001-10-09 13:00 subproject/hello
""")

        with cwd("unpack-dir", create=True):
            # Unpack archive
            p = run(["tar", "xf", "../superproject/archive.tar"])
            self.assertEqual(p.returncode, 0)

            # Check files in working directory
            self.assertFileContent("hello", b"content")
            self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = subproject
""")
            self.assertFileContent("subproject/.subproject", b"""\
[upstream]
\tobjectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
\turl = ../subproject
""")
            self.assertFileContent("subproject/hello", b"content")

            # And now the final test. Check subpatch commands!
            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(p.stdout, b"subproject\n")


if __name__ == '__main__':
    unittest.main()
