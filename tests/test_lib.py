#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import unittest
from os.path import abspath, dirname, join, realpath

from helpers import (Git, TestCaseHelper, TestCaseTempFolder,
                     create_git_repo_with_branches_and_tags, cwd, mkdir, touch)

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from subpatch import (AppException, ConfigLine, ErrorCode,
                      FindSuperprojectData, LineDataEmpty, LineDataHeader,
                      LineDataKeyValue, LineType, ObjectType, SCMType,
                      URLTypes, check_superproject_data, config_add_section2,
                      config_add_subproject, config_parse2, config_drop_key2,
                      config_drop_section_if_empty,
                      config_set_key_value2, config_unparse2,
                      gen_super_paths, gen_sub_paths_from_cwd_and_relpath,
                      gen_sub_paths_from_relpath,
                      find_superproject, get_name_from_repository_url,
                      get_url_type, git_diff_in_dir, git_diff_name_only,
                      git_get_object_type, git_get_sha1, git_get_toplevel,
                      git_init_and_fetch, git_ls_files_untracked,
                      git_ls_remote, git_ls_remote_guess_ref,
                      git_ls_tree_in_dir, git_verify, is_sha1,
                      is_valid_revision, parse_sha1_names, parse_z,
                      split_with_ts, split_with_ts_bytes)


class TestSplitWithTs(unittest.TestCase):
    def test_split_with_ts(self):
        self.assertEqual([], list(split_with_ts("")))
        self.assertEqual(["\n"], list(split_with_ts("\n")))
        self.assertEqual(["x"], list(split_with_ts("x")))
        self.assertEqual(["x\n"], list(split_with_ts("x\n")))
        self.assertEqual(["x\n", "y"], list(split_with_ts("x\ny")))
        self.assertEqual(["x\n", "y\n"], list(split_with_ts("x\ny\n")))

    def test_split_with_ts_bytes(self):
        self.assertEqual([], list(split_with_ts_bytes(b"")))
        self.assertEqual([b"\n"], list(split_with_ts_bytes(b"\n")))
        self.assertEqual([b"x"], list(split_with_ts_bytes(b"x")))
        self.assertEqual([b"x\n"], list(split_with_ts_bytes(b"x\n")))
        self.assertEqual([b"x\n", b"y"], list(split_with_ts_bytes(b"x\ny")))
        self.assertEqual([b"x\n", b"y\n"], list(split_with_ts_bytes(b"x\ny\n")))


class TestConfigAddSubproject(TestCaseTempFolder, TestCaseHelper):
    def test_empty(self):
        touch(".subpatch", b"")
        config_add_subproject(b".subpatch", b"a/b/c")
        self.assertFileContent(".subpatch", b"""\
[subprojects]
\tpath = a/b/c
""")

    def test_inserting(self):
        touch(".subpatch", b"""\
[core]
\tsome = setting
[subprojects]
\tpath = a/x
\tpath = c/x
""")
        config_add_subproject(b".subpatch", b"b/x")
        self.assertFileContent(".subpatch", b"""\
[core]
\tsome = setting
[subprojects]
\tpath = a/x
\tpath = b/x
\tpath = c/x
""")


class TestConfigParse2(unittest.TestCase):
    def compare(self, config, config_lines_expected):
        config_lines_actual = list(config_parse2(split_with_ts_bytes(config)))
        self.assertEqual(config_lines_actual, config_lines_expected),

    def test_comments(self):
        self.compare(b"", [])
        self.compare(b"\n",
                     [ConfigLine(b"\n", LineType.EMPTY, LineDataEmpty())])
        self.compare(b"# comment\n",
                     [ConfigLine(b"# comment\n", LineType.COMMENT, LineDataEmpty())])
        self.compare(b" # comment\n",
                     [ConfigLine(b" # comment\n", LineType.COMMENT, LineDataEmpty())])
        self.compare(b" ; comment\n",
                     [ConfigLine(b" ; comment\n", LineType.COMMENT, LineDataEmpty())])
        self.compare(b" \t; comment\n",
                     [ConfigLine(b" \t; comment\n", LineType.COMMENT, LineDataEmpty())])

    def test_section(self):
        self.compare(b" [name] \n",
                     [ConfigLine(b" [name] \n", LineType.HEADER, LineDataHeader(b"name", None))])
        self.compare(b" [name \"sub\" ] \n",
                     [ConfigLine(b" [name \"sub\" ] \n", LineType.HEADER, LineDataHeader(b"name", b"sub"))])
        self.compare(b"key=value\n",
                     [ConfigLine(b"key=value\n", LineType.KEY_VALUE, LineDataKeyValue(b"key", b"value"))])
        self.compare(b"  key\t=\tvalue  \n",
                     [ConfigLine(b"  key\t=\tvalue  \n", LineType.KEY_VALUE, LineDataKeyValue(b"key", b"value"))])

    def test_unparse(self):
        config_lines = [ConfigLine(b" ; comment\n", LineType.COMMENT, LineDataEmpty()),
                        ConfigLine(b" [name]\n", LineType.HEADER, LineDataHeader(b"name", None)),
                        ConfigLine(b"key=value\n", LineType.KEY_VALUE, LineDataKeyValue(b"key", b"value"))]
        self.assertEqual(config_unparse2(config_lines), b"""\
 ; comment
 [name]
key=value
""")


class TestConfigDropKey(unittest.TestCase):
    def compare(self, section, key, config, config_expected):
        config_lines = config_parse2(split_with_ts_bytes(config))
        config_lines_actual = config_drop_key2(config_lines, section, key)
        config_actual = config_unparse2(list(config_lines_actual))
        # TODO settle on consistent order. What should be exepted and whould should be actual!
        self.assertEqual(config_actual, config_expected)

    def test_simple(self):
        self.compare(b"section", b"key", b"""\
[section]
\tkey = x
""", b"""\
[section]
""")

    def test_complex(self):
        self.compare(b"b", b"key", b"""\
[a]
\tkey = x
[b]
\tkey = x
\tkey = x
[c]
\tkey = x
""", b"""\
[a]
\tkey = x
[b]
[c]
\tkey = x
""")


class TestConfigDropSectionIfEmpty(unittest.TestCase):
    def compare(self, section, config, config_expected):
        config_lines = config_parse2(split_with_ts_bytes(config))
        config_lines_actual = config_drop_section_if_empty(config_lines, section)
        config_actual = config_unparse2(list(config_lines_actual))
        # TODO settle on consistent order. What should be exepted and whould should be actual!
        self.assertEqual(config_actual, config_expected)

    def test_simple_drop(self):
        self.compare(b"section",  b"""\
[section]
""", b"""\
""")

    def test_simple_no_drop(self):
        self.compare(b"section",  b"""\
[section]
\tkey = value
""", b"""\
[section]
\tkey = value
""")

    def test_complex(self):
        self.compare(b"a",  b"""\
[a]
[b]
[c]
""", b"""\
[b]
[c]
""")
        self.compare(b"b",  b"""\
[a]
[b]
[c]
""", b"""\
[a]
[c]
""")
        self.compare(b"c",  b"""\
[a]
[b]
[c]
""", b"""\
[a]
[b]
""")


class TestConfigSetKeyValue2(unittest.TestCase):
    def compare(self, section, key, value, config, config_expected, append=False):
        config_lines = config_parse2(split_with_ts_bytes(config))
        config_lines_actual = config_set_key_value2(config_lines, section, key, value, append=append)
        config_actual = config_unparse2(list(config_lines_actual))
        # TODO settle on consistent order. What should be exepted and whould should be actual!
        self.assertEqual(config_actual, config_expected)

    def test_simple(self):
        self.compare(b"section", b"key", b"value", b"""\
[section]
""", b"""\
[section]
\tkey = value
""")

    def test_order_section(self):
        self.compare(b"b", b"key", b"value", b"""\
[a]
[b]
[c]
""", b"""\
[a]
[b]
\tkey = value
[c]
""")

    def test_order_keys(self):
        self.compare(b"section", b"b", b"2", b"""\
[section]
a = 1
c = 3
""", b"""\
[section]
a = 1
\tb = 2
c = 3
""")

    def test_key_replace(self):
        self.compare(b"section", b"b", b"4", b"""\
[section]
a = 1
b = 2
c = 3
""", b"""\
[section]
a = 1
\tb = 4
c = 3
""")

    def test_multiple_keys_replace(self):
        self.compare(b"section", b"key", b"3", b"""\
[section]
key = 1
key = 2
""", b"""\
[section]
\tkey = 3
""")

    def test_key_append(self):
        self.compare(b"section", b"key", b"2", b"""\
[section]
key = 1
key = 3
""", b"""\
[section]
key = 1
\tkey = 2
key = 3
""", append=True)

    def test_key_append_same_value(self):
        # NOTE: Implementation detail. If the value already exists, the new
        # value is appending after the first occurence.
        self.compare(b"section", b"key", b"value", b"""\
[section]
key = value
key = value
""", b"""\
[section]
key = value
\tkey = value
key = value
""", append=True)


class TestConfigAddSection2(unittest.TestCase):
    def compare(self, section, config, config_expected):
        config_lines = config_parse2(split_with_ts_bytes(config))
        config_lines_actual = config_add_section2(config_lines, section)
        config_actual = config_unparse2(list(config_lines_actual))
        self.assertEqual(config_actual, config_expected)

    def test_simple(self):
        self.compare(b"section", b"""\
""", b"""\
[section]
""")

    def test_order(self):
        self.compare(b"b", b"""\
[a]
[c]
""", b"""\
[a]
[b]
[c]
""")

    def test_already_exists(self):
        self.compare(b"section", b"""\
[section]
""", b"""\
[section]
""")


class TestFindSuperproject(TestCaseTempFolder):
    def test_search_ends_on_filesystem_boundary(self):
        # NOTE: Assumption that "/run/" is a tmpfs and "/" is not!
        with cwd("/run/"):
            # TODO find a way to test this. The abort was done because the
            # filesystem boundary was hit!
            data = find_superproject()
            self.assertEqual(data.super_path, None)
            self.assertEqual(data.scm_type, None)
            self.assertEqual(data.scm_path, None)

    def test_plain_superproject(self):
        # No configuration file in the path.
        abs_cwd = abspath(os.getcwdb())
        data = find_superproject()
        self.assertEqual(data.super_path, None)
        self.assertEqual(data.scm_type, None)
        self.assertEqual(data.scm_path, None)

        # A configuration file at the current work directory
        touch(".subpatch")
        data = find_superproject()
        self.assertEqual(data.super_path, abs_cwd)
        self.assertEqual(data.scm_type, None)
        self.assertEqual(data.scm_path, None)

        # A configuration file at a toplevel directory
        with cwd("a/b/c", create=True):
            data = find_superproject()
            self.assertEqual(data.super_path, abs_cwd)
            self.assertEqual(data.scm_type, None)
            self.assertEqual(data.scm_path, None)

    def test_git_superproject(self):
        abs_cwd = abspath(os.getcwdb())
        git = Git()
        git.init()
        data = find_superproject()
        self.assertEqual(data.super_path, None)
        self.assertEqual(data.scm_type, SCMType.GIT)
        self.assertEqual(data.scm_path, abs_cwd)

        # Now check in a subdirectory
        with cwd("a/b/c", create=True):
            data = find_superproject()
            self.assertEqual(data.super_path, None)
            self.assertEqual(data.scm_type, SCMType.GIT)
            self.assertEqual(data.scm_path, abs_cwd)

        # Now check with a configuration file
        touch(".subpatch")
        data = find_superproject()
        self.assertEqual(data.super_path, abs_cwd)
        self.assertEqual(data.scm_type, SCMType.GIT)
        self.assertEqual(data.scm_path, abs_cwd)

        with cwd("a/b/c"):
            data = find_superproject()
            self.assertEqual(data.super_path, abs_cwd)
            self.assertEqual(data.scm_type, SCMType.GIT)
            self.assertEqual(data.scm_path, abs_cwd)
            # Adding the subpatch config file makes it a PLAIN superproject.
            # TODO E.g. think about a superproject including a project that
            # uses subpatch.
            touch(".subpatch", b"")
            abs_cwd_sub = abspath(os.getcwdb())
            data = find_superproject()
            self.assertEqual(data.super_path, abs_cwd_sub)
            self.assertEqual(data.scm_type, SCMType.GIT)
            self.assertEqual(data.scm_path, abs_cwd)


class TestCheckSuperprojectData(TestCaseTempFolder):
    def test_no_scm_and_no_config(self):
        data = FindSuperprojectData(None, None, None)
        checked_data = check_superproject_data(data)
        self.assertIsNone(checked_data)

    def test_config_and_no_scm(self):
        data = FindSuperprojectData(b"/super", None, None)
        checked_data = check_superproject_data(data)
        self.assertEqual(checked_data.super_path, b"/super")
        self.assertEqual(checked_data.configured, True)
        self.assertEqual(checked_data.scm_type, None)

    def test_config_and_scm(self):
        data = FindSuperprojectData(b"/super", SCMType.GIT, b"/super")
        checked_data = check_superproject_data(data)
        self.assertEqual(checked_data.super_path, b"/super")
        self.assertEqual(checked_data.configured, True)
        self.assertEqual(checked_data.scm_type, SCMType.GIT)

    def test_no_config_and_scm(self):
        data = FindSuperprojectData(None, SCMType.GIT, b"/super")
        checked_data = check_superproject_data(data)
        self.assertEqual(checked_data.super_path, b"/super")
        self.assertEqual(checked_data.configured, False)
        self.assertEqual(checked_data.scm_type, SCMType.GIT)

    def test_missmatch_path(self):
        with self.assertRaises(AppException) as context:
            data = FindSuperprojectData(b"/a", SCMType.GIT, b"/b")
            check_superproject_data(data)
        self.assertEqual(context.exception.get_code(), ErrorCode.NOT_IMPLEMENTED_YET)


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
        self.assertIsNone(git_get_toplevel())

    def test_git_get_toplevel(self):
        with cwd("subproject", create=True):
            git = Git()
            git.init()
            touch("hello", b"content")
            git.add("hello")
            git.commit("msg")

            cur_cwd = os.getcwdb()
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

    def test_depth_for_git_init_and_fetch(self):
        with cwd("remote", create=True):
            git = Git()
            git.init()
            touch("file", b"a")
            git.add("file")
            git.commit("first commit")
            sha1_first_commit = git.get_sha1()
            sha1_first_tree = git.get_sha1("HEAD^{tree}")
            sha1_first_blob = git.get_sha1("HEAD:file")

            touch("file", b"b")
            git.add("file")
            git.commit("second commit")
            sha1_second_commit = git.get_sha1()
            sha1_second_tree = git.get_sha1("HEAD^{tree}")
            sha1_second_blob = git.get_sha1("HEAD:file")

        with cwd("local", create=True):
            git = Git()
            git.init()
            sha1 = git_init_and_fetch("../remote", "refs/heads/master")
            self.assertEqual(sha1, b"b8019be749b96c92c65ae2fdb99753670fd32cf9")

            # The top most (depth=1) objects are exist in the object store.
            self.assertTrue(git.object_exists(sha1_second_blob))
            self.assertTrue(git.object_exists(sha1_second_tree))
            self.assertTrue(git.object_exists(sha1_second_commit))

            # The other objects (depth>=2) objects do not exist in the object
            # store.
            self.assertFalse(git.object_exists(sha1_first_blob))
            self.assertFalse(git.object_exists(sha1_first_tree))
            self.assertFalse(git.object_exists(sha1_first_commit))

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

    def test_parse_sha1_names(self):
        self.assertEqual(parse_sha1_names(b"""\
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\tHEAD
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/heads/main
cccccccccccccccccccccccccccccccccccccccc\trefs/tags/v0.1a2
dddddddddddddddddddddddddddddddddddddddd\trefs/tags/v0.1a2^{}
""", sep=b"\t"), {b"HEAD": b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                  b"refs/heads/main": b"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                  b"refs/tags/v0.1a2": b"cccccccccccccccccccccccccccccccccccccccc",
                  b"refs/tags/v0.1a2^{}": b"dddddddddddddddddddddddddddddddddddddddd",
                  })

        # Empty file
        self.assertEqual(parse_sha1_names(b""), {})

        # With empty lines
        self.assertEqual(parse_sha1_names(b"\n\n\n"), {})

    def test_git_ls_remote_guess_ref(self):
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
        touch("a")
        git.add("a")
        git.commit("test")
        touch("a", b"x")
        self.assertEqual([b"a"], git_diff_name_only())
        self.assertEqual([], git_diff_name_only(staged=True))

        mkdir("b")
        touch("b/c")
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

        touch("a")
        self.assertEqual([b"a"], git_ls_files_untracked())

        touch("b")
        self.assertEqual([b"a", b"b"], git_ls_files_untracked())

        # Make the untracked file a tracked file
        git.add("a")
        # Now only one file is untracked
        self.assertEqual([b"b"], git_ls_files_untracked())

        # Make a untracked file that is ignored with gitignore
        touch("c")
        touch(".gitignore", b"c\n")
        git.add(".gitignore")
        # It should not show up in the untracked files list!
        self.assertEqual([b"b"], git_ls_files_untracked())

        # Create a untracked file in a directory
        with cwd("subdir", create=True):
            touch("d")

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

    def test_git_diff_in_dir(self):
        git = Git()
        git.init()
        top_dir = os.getcwdb()

        mkdir("dir")
        touch("dir/a")
        touch("b")
        git.add("dir/a")
        git.add("b")
        git.commit("add a and b")

        # Without any changes
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With unstaged changes in other part of the repo
        touch("b", b"changes")
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With staged changes in other part of the repo
        git.add("b")
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With unstaged changes in the subdir
        touch("dir/a", b"changes")
        self.assertTrue(git_diff_in_dir(top_dir, "dir"))
        self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertTrue(git_diff_in_dir(top_dir, "dir"))
            self.assertFalse(git_diff_in_dir(top_dir, "dir", staged=True))

        # With staged changes in the subdir
        git.add("dir/a")
        self.assertFalse(git_diff_in_dir(top_dir, "dir"))
        self.assertTrue(git_diff_in_dir(top_dir, "dir", staged=True))
        with cwd("dir"):
            self.assertFalse(git_diff_in_dir(top_dir, "dir"))
            self.assertTrue(git_diff_in_dir(top_dir, "dir", staged=True))

    def test_git_ls_tree_in_dir(self):
        git = Git()
        git.init()

        mkdir("dir")
        touch("dir/a")
        touch("b")
        git.add("dir/a")
        git.add("b")
        git.commit("add a and b")

        self.assertEqual([b"b", b"dir/a"], git_ls_tree_in_dir(b""))
        self.assertEqual([b"dir/a"], git_ls_tree_in_dir(b"dir"))
        self.assertEqual([], git_ls_tree_in_dir(b"does-not-exists-dir"))

        # If the cwd is a subdirectory, the output and the argument are still
        # relative to the toplevel of the repository.
        with cwd("dir"):
            self.assertEqual([b"b", b"dir/a"], git_ls_tree_in_dir(b""))
            self.assertEqual([b"dir/a"], git_ls_tree_in_dir(b"dir"))
            self.assertEqual([], git_ls_tree_in_dir(b"does-not-exists-dir"))

    def test_git_get_sha1(self):
        git = Git()
        git.init()
        git.call(["switch", "-c", "main", "-q"])

        touch("a", b"1")
        git.add("a")
        git.commit("add a")
        git.tag("v1", "msg")

        touch("a", b"2")
        git.add("a")
        git.commit("change a")

        self.assertEqual(git_get_sha1("HEAD"), b"4975f72e17be27d5e0d66dd3ec6ea9662de9046e")
        self.assertEqual(git_get_sha1("HEAD^"), b"e9a39bbb7a5057ad81ae413ed9b31a848e73b36a")
        self.assertEqual(git_get_sha1("v1"), b"e3471ab3cc16a5dc71317a5567929f172a88d763")
        self.assertEqual(git_get_sha1("main"), b"4975f72e17be27d5e0d66dd3ec6ea9662de9046e")


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
        self.assertEqual("name", f("http://localhost:7000/name/.git/"))

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


class TestGenSuperPaths(TestCaseTempFolder):
    def test_multiple_level_of_subdirectories(self):
        super_abspath = os.getcwdb()
        paths = gen_super_paths(super_abspath)
        self.assertEqual(paths.super_abspath, super_abspath)
        self.assertEqual(paths.super_to_cwd_relpath, b"")

        with cwd("sub1", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1")

        with cwd("sub1/sub2", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2")

        with cwd("sub1/sub2/sub3", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2/sub3")

        with cwd("sub1/sub2/sub3/sub4", create=True):
            paths = gen_super_paths(super_abspath)
            self.assertEqual(paths.super_abspath, super_abspath)
            self.assertEqual(paths.super_to_cwd_relpath, b"sub1/sub2/sub3/sub4")


class TestGenSubPaths(TestCaseTempFolder):
    def test_gen_sub_paths_from_relpath(self):
        super_abspath = os.getcwdb()
        super_paths = gen_super_paths(super_abspath)

        sub_paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
        self.assertEqual(sub_paths.super_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(sub_paths.cwd_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(sub_paths.sub_name, b"sub2")

        with cwd("sub1", create=True):
            super_paths = gen_super_paths(super_abspath)
            sub_paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(sub_paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(sub_paths.cwd_to_sub_relpath, b"sub2")
            self.assertEqual(sub_paths.sub_name, b"sub2")

        with cwd("sub1/sub2", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3/sub4", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_relpath(super_paths, b"sub1/sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"../..")
            self.assertEqual(paths.sub_name, b"sub2")

        # Special case for sub_name: superproject at the toplevel directory
        super_paths = gen_super_paths(super_abspath)
        paths = gen_sub_paths_from_relpath(super_paths, b"")
        self.assertEqual(paths.super_to_sub_relpath, b"")
        self.assertEqual(paths.cwd_to_sub_relpath, b"")
        self.assertEqual(paths.sub_name, b"")

    def test_multiple_level_of_subdirectories(self):
        super_abspath = os.getcwdb()

        super_paths = gen_super_paths(super_abspath)
        paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"sub1/sub2")
        self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(paths.cwd_to_sub_relpath, b"sub1/sub2")
        self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"sub2")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"sub2")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"..")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")
            self.assertEqual(paths.sub_name, b"sub2")

        with cwd("sub1/sub2/sub3/sub4", create=True):
            super_paths = gen_super_paths(super_abspath)
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"../..")
            self.assertEqual(paths.super_to_sub_relpath, b"sub1/sub2")
            self.assertEqual(paths.cwd_to_sub_relpath, b"../..")
            self.assertEqual(paths.sub_name, b"sub2")

        # Special case for sub_name: superproject at the toplevel directory
        super_paths = gen_super_paths(super_abspath)
        paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"")
        self.assertEqual(paths.super_to_sub_relpath, b"")
        self.assertEqual(paths.cwd_to_sub_relpath, b"")
        self.assertEqual(paths.sub_name, b"")

    def test_argument_is_normalized(self):
        super_abspath = os.getcwdb()
        super_paths = gen_super_paths(super_abspath)

        with cwd("sub1/sub2/", create=True):
            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"..")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")

            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b"../.")
            self.assertEqual(paths.cwd_to_sub_relpath, b"..")

            paths = gen_sub_paths_from_cwd_and_relpath(super_paths, b".")
            self.assertEqual(paths.cwd_to_sub_relpath, b"")


if __name__ == '__main__':
    unittest.main()
