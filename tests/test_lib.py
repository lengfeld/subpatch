#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import os
import unittest
import tempfile
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import join, realpath, dirname, abspath
from helpers import TestCaseTempFolder, cwd, touch, Git, \
                    create_git_repo_with_branches_and_tags

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from subpatch import git_get_toplevel, git_get_object_type, get_url_type, \
                     URLTypes, get_name_from_repository_url, \
                     git_init_and_fetch, is_sha1, ObjectType, git_ls_remote, \
                     git_ls_remote_guess_ref, git_verify, \
                     config_parse, config_add_section, split_with_ts, config_unparse, \
                     is_valid_revision


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


if __name__ == '__main__':
    unittest.main()
