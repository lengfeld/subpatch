#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, touch, Git, \
                    create_git_repo_with_branches_and_tags, mkdir

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from subpatch import git_get_toplevel, git_get_object_type, get_url_type, \
                     URLTypes, get_name_from_repository_url, \
                     git_init_and_fetch, is_sha1, ObjectType, git_ls_remote, \
                     git_ls_remote_guess_ref, git_verify, \
                     config_parse, config_add_section, split_with_ts, config_unparse, \
                     is_valid_revision, subprojects_parse, Subproject, \
                     git_diff_name_only, is_cwd_toplevel_directory, git_ls_files_untracked, \
                     parse_z


class TestConfigParse(unittest.TestCase):
    def test_split_with_ts(self):
        self.assertEqual([], list(split_with_ts("")))
        self.assertEqual(["\n"], list(split_with_ts("\n")))
        self.assertEqual(["x"], list(split_with_ts("x")))
        self.assertEqual(["x\n"], list(split_with_ts("x\n")))
        self.assertEqual(["x\n", "y"], list(split_with_ts("x\ny")))
        self.assertEqual(["x\n", "y\n"], list(split_with_ts("x\ny\n")))

    def test_parse(self):
        self.assertEqual([], list(config_parse([])))
        self.assertEqual([(1, "\n")], list(config_parse(["\n"])))
        self.assertEqual([(1, " \n")], list(config_parse([" \n"])))
        self.assertEqual([(1, "# comment")], list(config_parse(["# comment"])))
        self.assertEqual([(1, " # comment")], list(config_parse([" # comment"])))
        self.assertEqual([(1, " ; comment")], list(config_parse([" ; comment"])))
        self.assertEqual([(1, "\t; comment")], list(config_parse(["\t; comment"])))

        self.assertEqual([(2, " [name] \n", "name", None)],
                         list(config_parse([" [name] \n"])))
        self.assertEqual([(2, " [name \"sub\"] \n", "name", "sub")],
                         list(config_parse([" [name \"sub\"] \n"])))

        self.assertEqual([(3, "name = value\n", "name", "value")],
                         list(config_parse(["name = value\n"])))
        self.assertEqual([(3, "  name\t=\tvalue  \n", "name", "value")],
                         list(config_parse(["  name\t=\tvalue  \n"])))

    def test_unparse(self):
        self.assertEqual("", config_unparse([]))
        self.assertEqual("\n", config_unparse([(1, "\n")]))
        self.assertEqual("\t\n", config_unparse([(1, "\t\n")]))
        self.assertEqual("name = value", config_unparse([(3, "name = value", "name", "value")]))
        self.assertEqual("name = value\n", config_unparse([(3, "name = value\n", "name", "value")]))

    def test_add_section(self):
        parts_to_add = [(3, "name = value\n", "name", "value")]

        def test(config, result_ok):
            result_actual = config_add_section(config_parse(split_with_ts(config)),
                                               "a", "b", parts_to_add)
            self.assertEqual(list(result_actual), list(config_parse(split_with_ts(result_ok))))

        test("", """\
[a "b"]
name = value
""")

        test("""\
[a "a"]
""", """\
[a "a"]
[a "b"]
name = value
""")
        test("""\
[a "a"]
[a "c"]
""", """\
[a "a"]
[a "b"]
name = value
[a "c"]
""")

        test("""\
[b "a"]
""", """\
[a "b"]
name = value
[b "a"]
""")

        # TODO add this testcase
        #         test("""\
        # [a]
        # """, """\
        # [a]
        # [a "b"]
        # name = value
        # """)

        test("""\
[b]
""", """\
[a "b"]
name = value
[b]
""")


class TestSubprojectsParse(unittest.TestCase):
    def parse_from_string(self, s):
        # TODO Find better name for "string" and "s"
        lines = split_with_ts(s)
        config_parts = config_parse(lines)
        return list(subprojects_parse(config_parts))

    def test_empty(self):
        subprojects = self.parse_from_string("")
        self.assertEqual([], subprojects)

    def test_empty_lines(self):
        subprojects = self.parse_from_string("\n\n\n")
        self.assertEqual([], subprojects)

    def test_one(self):
        subprojects = self.parse_from_string("[subpatch \"test\"]\n")
        self.assertEqual(1, len(subprojects))
        self.assertEqual(subprojects[0], Subproject("test"))

    def test_one_with_values(self):
        subprojects = self.parse_from_string("""\
[subpatch \"subproject\"]
\turl = ../subproject
\trevision = v1
""")
        self.assertEqual(1, len(subprojects))
        self.assertEqual(subprojects[0],
                         Subproject("subproject", url="../subproject", revision="v1"))

    def test_non_subpatch_subsection(self):
        subprojects = self.parse_from_string("""\
[subpatch \"subprojectA\"]
[configbla \"somestuff\"]
\turl = ../subproject
[subpatch \"subprojectB\"]
""")
        self.assertEqual(2, len(subprojects))
        self.assertEqual(subprojects[0], Subproject("subprojectA"))
        self.assertEqual(subprojects[1], Subproject("subprojectB"))


class TestGit(TestCaseTempFolder):
    def test_is_sha1(self):
        self.assertTrue(is_sha1(b"32c32dcaa3c7f7024387640a91e98a5201e1f202"))
        self.assertFalse(is_sha1(b".2c32dcaa3c7f7024387640a91e98a5201e1f202"))

    def test_git_get_object_type(self):
        git = Git()
        git.init()
        touch("file", b"content")
        git.add("file")
        git.commit("message")
        git.tag("v1", "msg")

        self.assertEqual(ObjectType.COMMIT, git_get_object_type(b"HEAD"))
        self.assertEqual(ObjectType.TREE, git_get_object_type(b"HEAD^{tree}"))
        self.assertEqual(ObjectType.BLOB, git_get_object_type(b"HEAD:file"))
        self.assertEqual(ObjectType.TAG, git_get_object_type(b"v1"))
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

    def test_git_init_and_fetch(self):
        with cwd("remote", create=True):
            create_git_repo_with_branches_and_tags()

        with cwd("local", create=True):
            sha1 = git_init_and_fetch("../remote", "refs/tags/v1.1")
            self.assertEqual(b"e85c40dcd26466c0052323eb767d1a44ef0a12c1", sha1)
            self.assertEqual(ObjectType.TAG, git_get_object_type(sha1))

            sha1 = git_init_and_fetch("../remote", "refs/heads/v1-stable")
            self.assertEqual(b'32c32dcaa3c7f7024387640a91e98a5201e1f202', sha1)
            self.assertEqual(ObjectType.COMMIT, git_get_object_type(sha1))

            # TODO replace with specific git exception
            self.assertRaises(Exception, git_init_and_fetch,
                              "../remote", "refs/heads/does_not_exists")

    def test_git_ls_remote(self):
        with cwd("remote", create=True):
            create_git_repo_with_branches_and_tags()
            refs_sha1 = git_ls_remote(".")
        self.assertEqual([b'HEAD',
                          b'refs/heads/main', b'refs/heads/v1-stable',
                          b'refs/tags/v1', b'refs/tags/v1^{}',
                          b'refs/tags/v1.1', b'refs/tags/v1.1^{}',
                          b'refs/tags/v2', b'refs/tags/v2^{}'],
                         list(refs_sha1))
        self.assertEqual(b"60c7ec01d2a8d8c450896bb683c16637d52ea63c",
                         refs_sha1[b"refs/tags/v2"])
        self.assertEqual(b"e85c40dcd26466c0052323eb767d1a44ef0a12c1",
                         refs_sha1[b"refs/tags/v1.1"])

    def test_git_ls_remote(self):
        with cwd("remote", create=True):
            create_git_repo_with_branches_and_tags()

            self.assertEqual(b"refs/heads/main",
                             git_ls_remote_guess_ref(".", "main"))
            self.assertEqual(b"refs/heads/main",
                             git_ls_remote_guess_ref(".", "refs/heads/main"))
            self.assertEqual(b"refs/tags/v1",
                             git_ls_remote_guess_ref(".", "v1"))
            self.assertEqual(None, git_ls_remote_guess_ref(".", "v3"))

    def test_git_verify(self):
        # TODO Refactor to common code. Every tmp dir should be in /tmp!
        with tempfile.TemporaryDirectory() as tmpdirname:
            with cwd(tmpdirname):
                # TODO Exception should be replaced with a git specifc exception
                self.assertRaises(Exception, git_verify, "main")

        create_git_repo_with_branches_and_tags()
        self.assertEqual(True, git_verify("main"))
        self.assertEqual(False, git_verify("does-not-exists"))
        self.assertEqual(True, git_verify("v1"))
        self.assertEqual(True, git_verify("refs/tags/v1.1"))
        self.assertEqual(False, git_verify("00" * 20))

    def test_git_diff_name_only(self):
        git = Git()
        git.init()

        # NOTE: Only tracked and changed files are shown in "git diff"
        # Untracked files are not listed in "git diff"
        touch("a", b"")
        git.add("a")
        git.commit("test")
        touch("a", b"x")
        self.assertEqual([b"a"], git_diff_name_only())
        self.assertEqual([], git_diff_name_only(staged=True))

        mkdir("b")
        touch("b/c", b"")
        git.add("b/c")
        git.commit("test")
        touch("b/c", b"x")
        # 'a' has committed changes
        self.assertEqual([b"a", b"b/c"], git_diff_name_only())
        self.assertEqual([], git_diff_name_only(staged=True))

        git.add("a")
        self.assertEqual([b"b/c"], git_diff_name_only())
        self.assertEqual([b"a"], git_diff_name_only(staged=True))
        git.add("b/c")
        self.assertEqual([], git_diff_name_only())
        self.assertEqual([b"a", b"b/c"], git_diff_name_only(staged=True))

    def test_git_ls_files_untracked(self):
        git = Git()
        git.init()

        self.assertEqual([], git_ls_files_untracked())

        # TODO add touch without second argument
        touch("a", b"")
        self.assertEqual([b"a"], git_ls_files_untracked())

        touch("b", b"")
        self.assertEqual([b"a", b"b"], git_ls_files_untracked())

        # Make the untracked file a tracked file
        git.add("a")
        # Now only one file is untracked
        self.assertEqual([b"b"], git_ls_files_untracked())

        # Make a untracked file that is ignored with gitignore
        touch("c", b"")
        touch(".gitignore", b"c\n")
        git.add(".gitignore")
        # It should not show up in the untracked files list!
        self.assertEqual([b"b"], git_ls_files_untracked())

        # Create a untracked file in a directory
        with cwd("subdir", create=True):
            touch("d", b"")

        # NOTE: The config for "ls-files" only shows untracked dirs, not the
        # untracked files in the dirs.
        self.assertEqual([b"b", b"subdir/"], git_ls_files_untracked())

        with cwd("subdir"):
            # TODO: This is bad. It does not show the file "b" that is
            # untracked in the root of the git repo
            # "git ls-files" depends on the current work directory
            self.assertEqual([b"subdir/"], git_ls_files_untracked())

    def test_git_ls_files_untracked_ignore_files_in_di(self):
        # Special case found in the wild
        # git_ls_files_untracked() should not print directories that do only
        # contain ignored files. Happend with "__pycache__" dirs.
        git = Git()
        git.init()

        with cwd("__pycache__", create=True):
            touch("subpatch.cpython-310.pyc", b"something")
        self.assertEqual([b"__pycache__/"], git_ls_files_untracked())

        # Now make the file in the untracked directory ignored
        touch(".gitignore", b"*.pyc\n")
        git.add(".gitignore")
        git.commit("add gitignore")
        # And it's not listed anymore. Great!
        self.assertEqual([], git_ls_files_untracked())


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

    def test_is_valid_revision(self):
        self.assertTrue(is_valid_revision("main"))
        self.assertTrue(is_valid_revision("refs/heads/main"))
        self.assertTrue(is_valid_revision("v1.1"))
        self.assertTrue(is_valid_revision("177324cdffb43c57471674a4655a2a513ab158f5"))
        self.assertFalse(is_valid_revision("main\nxx"))
        self.assertFalse(is_valid_revision("main\tx"))
        self.assertFalse(is_valid_revision("\bmain"))

    def test_parse_z(self):
        self.assertEqual([], parse_z(b""))
        self.assertEqual([b""], parse_z(b"\0"))
        self.assertEqual([b"xx", b"yy"], parse_z(b"xx\0yy\0"))


class TestMisc(TestCaseTempFolder):
    def test_is_cwd_toplevel_directory(self):
        git = Git()
        git.init()

        super_abspath = git_get_toplevel()

        self.assertTrue(is_cwd_toplevel_directory(super_abspath))

        with cwd("subdir", create=True):
            self.assertFalse(is_cwd_toplevel_directory(super_abspath))


if __name__ == '__main__':
    unittest.main()
