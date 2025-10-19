#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import unittest
from subprocess import PIPE, Popen

from helpers import (Git, TestCaseHelper, TestCaseTempFolder, create_and_chdir,
                     create_git_repo_with_branches_and_tags, touch)
from localwebserver import FileRequestHandler, LocalWebserver


def create_git_repo_with_single_commit():
    git = Git()
    git.init()
    touch("hello", b"content")
    git.add("hello")
    git.commit("msg")


class TestSubmodule(TestCaseTempFolder, TestCaseHelper):
    def test_add_with_head_and_branch(self):
        with create_and_chdir("subproject"):
            create_git_repo_with_branches_and_tags()
            git = Git()

        with create_and_chdir("superproject"):
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
        with create_and_chdir("subproject"):
            create_git_repo_with_single_commit()

        with create_and_chdir("superproject"):
            create_git_repo_with_single_commit()
            git = Git()

            # NOTE/LEARNING: 'git submodule add' with relative path only works
            # in the toplevel directory!
            with create_and_chdir("folder"):
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

    def test_add_from_url(self):
        with create_and_chdir("subproject"):
            create_git_repo_with_single_commit()
            # Prepare repo for dump http protocol
            # See https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
            # TODO refactor combine with test_prog.py
            git = Git()
            git.call(["update-server-info"])

        with LocalWebserver(7000, FileRequestHandler), create_and_chdir("superproject"):
            create_git_repo_with_single_commit()
            git = Git()

            git.submodule(["-q", "add", "http://localhost:7000/subproject/.git/", "subproject1"])
            git.submodule(["-q", "add", "http://localhost:7000/subproject/.git", "subproject2"])
            # NOTE: The URL is taken verbatim. The leading slash is not changed
            # by 'git' before writing it in to config file.
            self.assertFileContent(".gitmodules",
                                   b"""\
[submodule "subproject1"]
\tpath = subproject1
\turl = http://localhost:7000/subproject/.git/
[submodule "subproject2"]
\tpath = subproject2
\turl = http://localhost:7000/subproject/.git
""")


if __name__ == '__main__':
    unittest.main()
