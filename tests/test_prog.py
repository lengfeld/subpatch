#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from copy import deepcopy
from time import sleep
from subprocess import Popen, PIPE, DEVNULL, call, run
from os.path import join, realpath, dirname, abspath
from localwebserver import LocalWebserver, FileRequestHandler
from helpers import TestCaseTempFolder, cwd, touch, Git, TestCaseHelper, \
                    create_git_repo_with_branches_and_tags


path = realpath(__file__)
SUBPATCH_PATH = join(dirname(path), "..", "subpatch")

# TODO This is ugly. The test for the command line tool "subpatch" should not
# need to include Subpatch itself. The git tooling should be moved into a
# seperated file.
sys.path.append(join(dirname(path), "../"))
from subpatch import ObjectType, git_get_object_type, git_ls_files_untracked


class TestSubpatch(TestCaseTempFolder):
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
license:   GPL-2.0-only
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
        sleep(0.50)
        from signal import SIGINT
        p.send_signal(SIGINT)

        _, stderr = p.communicate()
        self.assertEqual(3, p.returncode)
        self.assertEqual(b"Interrupted!\n", stderr)


class TestHelp(TestCaseHelper, TestSubpatch):
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


class TestCmdList(TestCaseHelper, TestSubpatch):
    def test_no_subpatch_config_file(self):
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
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
            self.run_subpatch_ok(["add", "../subproject", "first"], stdout=DEVNULL)

            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(b"first\n", p.stdout)

            self.run_subpatch_ok(["add", "../subproject", "external/second"], stdout=DEVNULL)

            p = self.run_subpatch_ok(["list"], stdout=PIPE)
            self.assertEqual(b"external/second\nfirst\n", p.stdout)

    def test_order_is_the_same_as_in_config(self):
        git = Git()
        git.init()
        with open(".subpatch", "bw") as f:
            f.write(b"""\
[subpatch "c_not"]
[subpatch "b_in"]
[subpatch "a_alphabetical_order"]
""")

        # TODO add command to check that this handmade config is valid!

        p = self.run_subpatch_ok(["list"], stdout=PIPE)
        self.assertEqual(b"c_not\nb_in\na_alphabetical_order\n", p.stdout)


class TestCmdStatus(TestCaseHelper, TestSubpatch):
    def test_no_subpatch_config_file(self):
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["status"], stderr=PIPE)
            self.assertEqual(b"Error: subpatch not yet configured for superproject!\n",
                             p.stderr)
            self.assertEqual(p.returncode, 4)

    def test_not_in_toplevel_directory(self):
        git = Git()
        git.init()

        touch(".subpatch")

        with cwd("subdir", create=True):
            p = self.run_subpatch(["status"], stderr=PIPE)
            self.assertEqual(b"Error: Feature not implemented yet: Current work directory must be the toplevel directory of the repo for now!\n",
                             p.stderr)
            self.assertEqual(p.returncode, 4)

    def test_two_clean_subprojects(self):
        create_super_and_subproject()
        with cwd("superproject"):
            self.run_subpatch_ok(["add", "../subproject", "subproject1"], stdout=DEVNULL)
            self.run_subpatch_ok(["add", "../subproject", "subproject2"], stdout=DEVNULL)
            git = Git()
            git.commit("add two subprojects")

            p = self.run_subpatch_ok(["status"], stdout=PIPE)
            self.assertEqual(b"""\
NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
NOTE: The format is markdown currently. Will mostly change in the future.

# subproject at 'subproject1'

* was integrated from URL: ../subproject

# subproject at 'subproject2'

* was integrated from URL: ../subproject
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

            self.run_subpatch_ok(["add", "../subproject"], stdout=DEVNULL)
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


class TestCmdAdd(TestCaseHelper, TestSubpatch):
    def test_not_in_superproject(self):
        # NOTE this does not fail, because the tmp folder is in the git folder
        # of the subpatch project itself.
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                p = self.run_subpatch(["add", "../ignore"], stderr=PIPE)
                self.assertEqual(b"Error: subpatch not yet configured for superproject!\n",
                                 p.stderr)
                self.assertEqual(p.returncode, 4)

    def test_without_url_arg(self):
        p = self.run_subpatch(["add"], stderr=PIPE)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"the following arguments are required: url", p.stderr)

    def test_adding_two_subproject(self):
        create_super_and_subproject()

        with cwd("superproject"):
            p = self.run_subpatch(["add", "../subproject", "dirB"], stdout=DEVNULL)
            self.assertEqual(0, p.returncode)
            p = self.run_subpatch(["add", "../subproject", "dirA"], stdout=DEVNULL)
            self.assertEqual(0, p.returncode)

            self.assertFileContent(".subpatch",
                                   b"""\
[subpatch \"dirA\"]
\turl = ../subproject
[subpatch \"dirB\"]
\turl = ../subproject
""")

            git = Git()
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tdirA/hello",
                              b"A\tdirB/hello"])

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

            self.run_subpatch_ok(["add", "../subproject"], stdout=PIPE)
            self.assertFileContent("subproject/a", b"")
            self.assertFileContent("subproject/.gitignore", b"a\n")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tsubproject/.gitignore",
                              b"A\tsubproject/a"])

    def test_subproject_directory_already_exists(self):
        create_super_and_subproject()

        with cwd("superproject"):
            # Just create a file. It should also fail!
            touch("subproject")

            p = self.run_subpatch(["add", "../subproject"], stderr=PIPE)
            self.assertEqual(b"Error: File 'subproject' alreay exists. Cannot add subproject!\n", p.stderr)
            self.assertEqual(4, p.returncode)

    def test_add_with_trailing_slash(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            p = self.run_subpatch_ok(["add", "../subproject/"], stdout=PIPE)
            self.assertIn(b"Adding subproject 'subproject' from URL '../subproject/' at revision 'HEAD'... Done.",
                          p.stdout)
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
                # NOTE: This also tests that "/.git/" is not used as the local
                # directory name.
                p = self.run_subpatch_ok(["add", "http://localhost:8000/subproject/.git/"], stdout=PIPE)
                self.assertIn(b"Adding subproject 'subproject' from URL 'http://localhost:8000/subproject/.git/' at revision 'HEAD'... Done",
                              p.stdout)
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
Adding subproject 'subproject' from URL '../subproject' at revision 'HEAD'... Done.
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
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
            self.assertEqual(b"Error: Invalid argument: path is empty\n",
                             p.stderr)

    def test_absolute_paths_are_not_supported(self):
        create_super_and_subproject()
        with cwd("superproject"):
            git = Git()
            p = self.run_subpatch(["add", "/tmp/subproject"], stdout=DEVNULL, stderr=PIPE)
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

            # TODO Implemented "--quiet"
            p = self.run_subpatch(["add", "../subproject", "-r", "master"], stdout=PIPE, stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: The reference 'master' cannot be resolved to a branch or tag!\n",
                             p.stderr)

            # TODO add test without "-r" argument. The internal code behaves differently!

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

            p = self.run_subpatch(["add", "../subproject", "-r", "main-does-not-exists"], stdout=DEVNULL, stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: The reference 'main-does-not-exists' cannot be resolved to a branch or tag!\n",
                             p.stderr)

            invalid_object_id = b"0" * 40
            p = self.run_subpatch(["add", "../subproject", "-r", invalid_object_id], stdout=DEVNULL, stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: Object id '0000000000000000000000000000000000000000' does not point to a valid object!\n",
                             p.stderr)

            p = self.run_subpatch(["add", "../subproject", "-r", object_id_file], stdout=DEVNULL, stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: Object id '177324cdffb43c57471674a4655a2a513ab158f5' does not point to a commit or tag object!\n",
                             p.stderr)

            p = self.run_subpatch(["add", "../subproject", "-r", "refs/heads\nmain"], stderr=PIPE)
            self.assertEqual(4, p.returncode)
            self.assertEqual(b"Error: Invalid argument: revision 'refs/heads\nmain' is invalid\n",
                             p.stderr)

    def test_with_revision(self):
        with cwd("subproject", create=True):
            create_git_repo_with_branches_and_tags()
            git = Git()
            object_id_commit = git.get_sha1("v1-stable")
            self.assertEqual(ObjectType.COMMIT, git_get_object_type(object_id_commit))
            object_id_tag = git.get_sha1("v2")
            self.assertEqual(ObjectType.TAG, git_get_object_type(object_id_tag))

        with cwd("superproject", create=True):
            git = Git()
            git.init()

            p = self.run_subpatch_ok(["add", "../subproject", "-r", "refs/heads/main"], stdout=PIPE)
            # NOTE: Checking the stdout here for a single time. There was a bug
            # in git_reset_hard().
            self.assertEqual(b"""\
Adding subproject 'subproject' from URL '../subproject' at revision 'refs/heads/main'... Done.
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""",
                             p.stdout)
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"change on main")
            self.assertFileContent(".subpatch", b"""\
[subpatch \"subproject\"]
\turl = ../subproject
\trevision = refs/heads/main
""")
            git.call(["reset", "--merge"])  # Remove all stagged changes

            p = self.run_subpatch_ok(["add", "../subproject", "-r", "v1"], stdout=DEVNULL)
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"initial")
            self.assertFileContent(".subpatch", b"""\
[subpatch \"subproject\"]
\turl = ../subproject
\trevision = v1
""")
            git.call(["reset", "--merge"])  # Remove all stagged changes

            p = self.run_subpatch_ok(["add", "../subproject", "-r", object_id_commit], stdout=DEVNULL)
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"change on stable")
            self.assertFileContent(".subpatch", b"""\
[subpatch \"subproject\"]
\turl = ../subproject
\trevision = %s
""" % (object_id_commit,))
            git.call(["reset", "--merge"])  # Remove all stagged changes

            p = self.run_subpatch_ok(["add", "../subproject", "-r", object_id_tag], stdout=DEVNULL)
            self.assertFileExistsAndIsDir("subproject")
            self.assertFileContent("subproject/file", b"change on main")
            self.assertFileContent(".subpatch", b"""\
[subpatch \"subproject\"]
\turl = ../subproject
\trevision = %s
""" % (object_id_tag,))
            git.call(["reset", "--merge"])  # Remove all stagged changes

            # Special case: Test revision argument with subdirectory for
            # subproject. This was broken.
            p = self.run_subpatch_ok(["add", "-r", "v1", "../subproject", "subdir/subproject"], stdout=DEVNULL)
            self.assertFileExistsAndIsDir("subdir/subproject")
            self.assertFileContent("subdir/subproject/file", b"initial")
            self.assertFileContent(".subpatch", b"""\
[subpatch \"subdir/subproject\"]
\turl = ../subproject
\trevision = v1
""")
            git.call(["reset", "--merge"])  # Remove all stagged changes


class TestCmdUpdate(TestCaseHelper, TestSubpatch):
    def test_some_errors_cases(self):
        with cwd("subproject", create=True):
            create_git_repo_with_branches_and_tags()

        with cwd("superproject", create=True):
            git = Git()
            git.init()
            self.run_subpatch_ok(["add", "-r", "v1", "../subproject", "dir/subproject"], stdout=DEVNULL)
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

            # Revert changes
            git.call(["reset", "--merge"])

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
            self.run_subpatch_ok(["add", "-r", "v1", "../subproject", "dir/subproject"], stdout=DEVNULL)
            self.assertFileContent(".subpatch", b"""\
[subpatch \"dir/subproject\"]
\turl = ../subproject
\trevision = v1
""")
            self.assertFileExistsAndIsDir("dir/subproject/dir")
            self.assertFileContent("dir/subproject/a", b"first-toplevel\n")
            self.assertFileContent("dir/subproject/dir/b", b"first\n")
            self.assertEqual(git.diff_staged_files(),
                             [b"A\t.subpatch",
                              b"A\tdir/subproject/.gitignore",
                              b"A\tdir/subproject/a",
                              b"A\tdir/subproject/dir/b",
                              b"A\tdir/subproject/dir/c",
                              b"A\tdir/subproject/dir/d",
                              b"A\tdir/subproject/dir/dir1/f"])
            git.commit("add subproject")

            p = self.run_subpatch(["update", "dir/subproject", "-r", "v2"], stdout=DEVNULL)
            self.assertEqual(0, p.returncode)

            self.assertFileContent(".subpatch", b"""\
[subpatch \"dir/subproject\"]
\turl = ../subproject
\trevision = v2
""")
            self.assertEqual(git.diff_staged_files(),
                             [b"M\t.subpatch",
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
diff --git a/.subpatch b/.subpatch
index 3453c2c..421a273 100644
--- a/.subpatch
+++ b/.subpatch
@@ -1,3 +1,3 @@
 [subpatch "dir/subproject"]
 \turl = ../subproject
-\trevision = v1
+\trevision = v2
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
            p = self.run_subpatch(["add", "-r", "v1", "../subproject", "subproject"], stdout=DEVNULL)
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
- To inspect the changes, use `git status` and `git diff --staged`.
- If you want to keep the changes, commit them with `git commit`.
- If you want to revert the changes, execute `git reset --merge`.
""")
            git.commit("adding subproject")

            p = self.run_subpatch_ok(["update", "subproject", "-r", "v2"], stdout=PIPE)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"""\
Updating subproject 'subproject' from URL '../subproject' to revision 'v2'... Done.
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

        with LocalWebserver(8000, FileRequestHandler), cwd("superproject", create=True):
            git = Git()
            git.init()
            p = self.run_subpatch(["add", "-r", "v1", "http://localhost:8000/subproject/.git/", "dir/subproject"], stdout=DEVNULL, hack=True)
            self.assertEqual(p.returncode, 0)
            git.commit("add subproject")

            # Get reference diff
            p = self.run_subpatch(["update", "dir/subproject", "-r", "v2"], stdout=DEVNULL, hack=True)
            self.assertEqual(p.returncode, 0)

            diff_ok = git.diff(staged=True)
            git.call(["reset", "--merge"])  # Cleanup

            with cwd("dir"):
                p = self.run_subpatch(["update", "subproject", "-r", "v2"], stdout=PIPE, hack=True)
                self.assertEqual(p.returncode, 0)
                # NOTE: Path in output is relative to the current work directory!
                self.assertEqual(p.stdout, b"""\
Updating subproject 'subproject' from URL 'http://localhost:8000/subproject/.git/' to revision 'v2'... Done.
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
            self.run_subpatch_ok(["add", "../subproject"], stdout=DEVNULL)
            self.assertFileContent(".subpatch", b"""\
[subpatch \"subproject\"]
\turl = ../subproject
""")
            git.commit("add subsproject")

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
            self.assertEqual(git.diff_staged_files(), [b"A\tsubproject/b"])


class TestNoGit(TestCaseHelper, TestSubpatch):
    def test_git_archive_export(self):
        # TODO combine tmpdir and cwd!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                create_super_and_subproject()
                with cwd("superproject"):
                    git = Git()
                    # TODO Use "-q/--quiet" argumnetk
                    self.run_subpatch_ok(["add", "../subproject"], stdout=DEVNULL)
                    git.commit("add subproject")

                    git.call(["archive", "-o", "archive.tar", "HEAD"])

                    # check archiv:
                    p = run(["tar", "tvf", "archive.tar"], stdout=PIPE)
                    self.assertEqual(p.returncode, 0)
                    self.assertEqual(p.stdout, b"""\
-rw-rw-r-- root/root        45 2001-10-09 13:00 .subpatch
-rw-rw-r-- root/root         7 2001-10-09 13:00 hello
drwxrwxr-x root/root         0 2001-10-09 13:00 subproject/
-rw-rw-r-- root/root         7 2001-10-09 13:00 subproject/hello
""")

                with cwd("unpack-dir", create=True):
                    # Unpack archive
                    p = run(["tar", "xf", "../superproject/archive.tar"])
                    self.assertEqual(p.returncode, 0)

                    # Check files in working directory
                    self.assertFileContent("hello", b"content")
                    self.assertFileContent("subproject/hello", b"content")
                    self.assertFileContent(".subpatch", b"""\
[subpatch \"subproject\"]
\turl = ../subproject
""")

                    # And now the final test. Check subpatch commands!
                    p = self.run_subpatch_ok(["list"], stdout=PIPE)
                    self.assertEqual(p.stdout, b"subproject\n")


if __name__ == '__main__':
    unittest.main()
