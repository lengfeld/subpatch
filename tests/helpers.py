#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import contextlib
import os
import shutil
import sys
import tempfile
import unittest
import configparser
from contextlib import chdir
from dataclasses import dataclass
from subprocess import DEVNULL, PIPE, Popen

# TODO unify
# NOTES
# - Paths/filenames are python <string> objects/types
# - file content is python <bytes> object


# In the current directory, create a git repo with two branches and a tag
# TODO Add self argument and checks for stable commit ids
# Some users depend on stable commit ids already.
def create_git_repo_with_branches_and_tags():
    git = Git()
    git.init()
    git.call(["switch", "-c", "main", "-q"])
    touch("file", b"initial")
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


# TODO copied from subpatch. Unify again
def parse_z(b):
    if b == b"":
        # Special case. b"".split(b"\0") is [b""], but
        # we want a list without elements here.
        return []

    return b.rstrip(b"\0").split(b"\0")


# TODO this function uses 'str' types, but actually we use the bytes type for
# this data a lot.
def get_prop_from_ini(filename: str, section: str, name: str) -> str | None:
    # We use the configparser here, because the git config file format is very
    # similar to INI format. It's a easy and fast way to get values from the
    # config file. E.g. faster than use "git config -f <filename> <prop>" as an
    # external command.
    data = configparser.ConfigParser()
    data.read(filename)
    try:
        return data[section][name]
    except KeyError:
        return None


# TODO Make this to GitExtra or GitTests and also have a Git class in
# subpatch.py.
# TODO convert to class to seperate functions as in git.py
class Git:
    def __init__(self):
        env = dict(os.environ)  # Get and copy the current environment

        # Only for unittests. So commit doesn't complain about empty user and
        # email.
        # Use different names for author and committer and different dates.
        # They should not be the same, because this had already masked a bug in
        # the code.  Using GIT_*_DATE makes SHA1 sum reproducable accross all
        # unit tests.
        env[b"GIT_AUTHOR_NAME"] = "OTHER other"
        env[b"GIT_AUTHOR_EMAIL"] = "other@example.com"
        env[b"GIT_AUTHOR_DATE"] = b"01 Oct 2016 14:00:00 +0800"
        env[b"GIT_COMMITTER_NAME"] = b"GIT git"
        env[b"GIT_COMMITTER_EMAIL"] = b"git@example.com"
        env[b"GIT_COMMITTER_DATE"] = b"09 Oct 2001 13:00:00 +0200"

        self._env = env

    def init(self):
        self.call(["init", "-q"])

    def add(self, filename):
        # TODO rework argument to be filenames as a list.
        self.call(["add", filename])

    def rm(self, filename):
        # TODO rework argument to be filenames as a list.
        self.call(["rm", "-q", filename])

    def tag(self, name, message):
        self.call(["tag", name, "-m", message])

    # Returns the SHA1 checksum as a bytes object without trailing newline!
    # TODO copied to "subpatch.py" -> refactor
    def get_sha1(self, rev="HEAD"):
        # NOTE: Special case for valid SHA1 sums. Even if the object for the
        # SHA1 does not exist in the repo, it's return as a valid SHA1 If the
        # rev is a too short SHA1, it's extend to a full SHA1 if a object with
        # the short SHA1 exists in the repo.
        p = Popen(["git", "rev-parse", "-q", "--verify", rev], stdout=PIPE, env=self._env)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("error here TODO")

        return stdout.rstrip(b"\n")

    def commit(self, msg):
        self.call(["commit", "-m", msg, "-q"])

    def commit_all(self, msg):
        self.call(["commit", "-a", "-m", msg, "-q"])

    SUBMODULE_EXTRA_ARGS = ["-c", "protocol.file.allow=always"]

    def submodule(self, args):
        # Fix an issue here: Fails with "file not supported" when running as
        # tests:
        # * https://github.com/flatpak/flatpak-builder/issues/495
        # * https://lists.archlinux.org/archives/list/arch-dev-public@lists.archlinux.org/thread/YYY6KN2BJH7KR722GF26SEWNXPLAANNQ/
        # It works as a normal user, but not in the test code. Add
        # 'allow=always' to fix this.
        self.call(self.SUBMODULE_EXTRA_ARGS + ["submodule"] + args)

    @dataclass
    class CallData:
        returncode: int
        stdout: bytes = None

    # TODO maybe name "run", because of "runSubpatch"
    def call(self, args, capture_stdout=False):
        stdout = None
        if capture_stdout:
            stdout = PIPE

        p = Popen(["git"] + args, env=self._env, stdout=stdout)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("error here")

        data = self.CallData(p.returncode)
        if capture_stdout:
            data.stdout = stdout

        return data

    def version(self):
        p = self.call(["version"], capture_stdout=True)
        if not p.stdout.startswith(b"git version "):
            raise Exception("tbd")
        # TODO Cache the version
        return p.stdout[12:].rstrip(b"\n")

    def diff_staged_files(self):
        # TODO use '\0' delimeter instead of '\n'
        # TODO use call()
        # TODO merge with code in "subpatch.py"
        p = Popen(["git", "diff", "--name-status", "--staged"], stdout=PIPE, env=self._env)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("error here")

        if stdout == b"":
            return []
        else:
            return stdout.rstrip(b"\n").split(b"\n")

    def diff(self, staged=False):
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        p = Popen(cmd, stdout=PIPE, env=self._env)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("error here")

        return stdout

    def cat_file(self, rev):
        p = Popen(["git", "cat-file", "-p", rev], stdout=PIPE, env=self._env)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("error here")

        return stdout

    def object_exists(self, sha1):
        # TODO check argument sha1 for a valid sha1. Otherwise the command does
        # not make sense.
        p = Popen(["git", "cat-file", "-e", sha1], stderr=DEVNULL, env=self._env)
        p.communicate()
        if p.returncode not in [0, 1]:
            raise Exception("error here")

        return p.returncode == 0

    def remove_staged_changes(self):
        self.call(["reset", "--merge"])


def touch(filename, content=b""):
    with open(filename, "bw") as f:
        f.write(content)


def mkdir(filename):
    os.mkdir(filename)


class TestCaseTempFolder(unittest.TestCase):
    @classmethod
    def tearDown(cls):
        os.chdir(cls.old_cwd)
        shutil.rmtree(cls.tmpdir)

    # Setup stuff is only called once before execution of all unittests in this
    # class, because it's setUpClass() and not setUp().
    @classmethod
    def setUp(cls):
        # cls.__name__ will be the name of the lower class.
        prefix = "subpatch-" + cls.__name__
        # NOTE: argument dir is not used, os it's 'None'
        # So the platform dependend directory is used. See
        # https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp
        # Important: The ecpectation is that this directory is not inside a
        # SCM, e.g. git. subpatch relys on the fact! Otherwise a lot of tests
        # will fail.
        # TODO Try to use: tempfile.TemporaryDirectory context
        cls.tmpdir = tempfile.mkdtemp(prefix=prefix)
        cls.old_cwd = os.getcwd()
        os.chdir(cls.tmpdir)


# TODO add "file" or "filesystem" or "dir" in name
class TestCaseHelper(unittest.TestCase):
    def assertFileExists(self, filename):
        # TODO add better explanation if something goes wrong!
        self.assertTrue(os.path.exists(filename))

    def assertFileDoesNotExist(self, filename):
        self.assertFalse(os.path.exists(filename))

    def assertFileExistsAndIsDir(self, filename):
        self.assertTrue(os.path.isdir(filename))

    def assertFileContent(self, filename, content_expected):
        with open(filename, "br") as f:
            content_actual = f.read()

            # TOOD unify debug env variable
            if os.environ.get("DEBUG", "0") == "1":
                print("file content of '%s':" % (filename,))
                sys.stdout.flush()
                sys.stdout.buffer.write(content_actual)
                sys.stdout.buffer.flush()

            self.assertEqual(content_actual, content_expected)


@contextlib.contextmanager
def create_and_chdir(path):
    os.makedirs(path)
    with chdir(path):
        yield 
