#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

# TODO reduce imports
import sys
import unittest
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, mkdir, touch, Git, TestCaseHelper


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
    def test_add(self):
        mkdir("subproject")
        with cwd("subproject"):
            create_git_repo_with_branches_and_tags()
            git = Git()
            sha1_tag_v1 = git.getSHA1("v1")

        mkdir("superproject")
        with cwd("superproject"):
            create_git_repo_with_single_commit()
            git = Git()
            # Fix an issue here: Fails with "file not supported"
            # * https://github.com/flatpak/flatpak-builder/issues/495
            # * https://lists.archlinux.org/archives/list/arch-dev-public@lists.archlinux.org/thread/YYY6KN2BJH7KR722GF26SEWNXPLAANNQ/
            # It works as a normal user, but not in the test code. Add allow
            # always.
            git.call(["-c", "protocol.file.allow=always", "submodule", "-q", "add", "../subproject/", "subproject1"])
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
            # NOTE: There is no way to directly specific a tag name or a commit
            # object. Only branches with the argument "-b" are supported!
            # And this branch name is then added to the config file.
            git.call(["-c", "protocol.file.allow=always", "submodule", "add", "-q", "-b", "v1-stable", "../subproject/", "subproject2"])
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


if __name__ == '__main__':
    unittest.main()
