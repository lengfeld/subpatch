#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

# TODO reduce imports
import sys
import unittest
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, touch, Git, TestCaseHelper


# In the current directory, createa a git repo with two branches and a tag
def create_git_repo_with_branches_and_tags():
    git = Git()
    git.init()
    git.call(["switch", "-c", "main", "-q"])
    touch("file", b"inital")
    git.add("file")
    git.commit("initial commit")
    git.tag("v1", "initial release")

    touch("file", b"change on main")
    git.add("file")
    git.commit("change on main")
    git.tag("v2", "new release after change")

    git.call(["switch", "-c", "v1-stable", "v1", "-q"])
    touch("file", b"change on stable")
    git.add("file")
    git.commit("change on stable")
    git.tag("v1.1", "new release on stable")

    # Switch HEAD back to 'main' branch
    git.call(["switch", "-q", "main"])


def create_git_repo_with_single_commit():
    git = Git()
    git.init()
    touch("hello", b"content")
    git.add("hello")
    git.commit("msg")


class TestSubmodule(TestCaseTempFolder, TestCaseHelper):
    def test_add_with_head_and_branch(self):
        with cwd("subproject", create=True):
            create_git_repo_with_branches_and_tags()
            git = Git()
            sha1_tag_v1 = git.getSHA1("v1")

        with cwd("superproject", create=True):
            create_git_repo_with_single_commit()
            git = Git()
            git.submodule(["-q", "add", "../subproject/", "subproject1"])
            self.assertFileExistsAndIsDir("subproject1")

            # By default submodule uses the HEAD of the subproject. This points
            # to the main branch!
            self.assertFileContent("subproject1/file", b"change on main")
            self.assertFileContent(".gitmodules",
                                   b"""\
[submodule "subproject1"]
\tpath = subproject1
\turl = ../subproject/
""")
            # "submodule add" does not make a final commit. It only downloads the files
            # and stages the changes. Finish with a commit object.
            git.commit_all("add subproject1")

            # Adding the same subproject a second time, but with a different
            # branch and into a different directory.
            # NOTE/LEARNING: There is no way to directly specific a tag name or
            # a commit object. Only branches with the argument "-b" are
            # supported!  And this branch name is then added to the config
            # file.
            git.submodule(["add", "-q", "-b", "v1-stable", "../subproject/", "subproject2"])
            self.assertFileContent("subproject2/file", b"change on stable")
            self.assertFileContent(".gitmodules",
                                   b"""\
[submodule "subproject1"]
\tpath = subproject1
\turl = ../subproject/
[submodule "subproject2"]
\tpath = subproject2
\turl = ../subproject/
\tbranch = v1-stable
""")
            git.commit_all("add subproject2")

    def test_add_in_subdir_fails(self):
        with cwd("subproject", create=True):
            create_git_repo_with_single_commit()

        with cwd("superproject", create=True):
            create_git_repo_with_single_commit()
            git = Git()

            # NOTE/LEARNING: 'git submodule add' with relative path only works
            # in the toplevel directory!
            with cwd("folder", create=True):
                # TODO "git.submodule()" and others methods do not have an
                # interface for failing commands. So fallback to popen here.
                p = Popen(["git"] + Git.SUBMODULE_EXTRA_ARGS + ["submodule", "add", "../../subproject/"],
                          stderr=PIPE)
                _, stderr = p.communicate()
                self.assertEqual(128, p.returncode)
                self.assertEqual(b"fatal: Relative path can only be used from the toplevel of the working tree\n",
                                 stderr)

            # But you can be in the toplevel directory and specific a subdirectory!
            git.submodule(["add", "-q", "../subproject/", "folder/subproject"])
            self.assertFileContent("folder/subproject/hello", b"content")
            self.assertFileContent(".gitmodules",
                                   b"""\
[submodule "folder/subproject"]
\tpath = folder/subproject
\turl = ../subproject/
""")


if __name__ == '__main__':
    unittest.main()
