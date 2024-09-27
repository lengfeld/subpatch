#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import sys
import shutil
import tempfile
import unittest
import contextlib
from subprocess import Popen, PIPE, DEVNULL, call
from os.path import isfile, isdir, join, realpath, dirname


# TODO unify
# NOTES
# - Paths/filenames are python <string> objects/types
# - file content is python <bytes> object


class Git():
    def init(self):
        self.call(["init", "-q"])

    def add(self, filename):
        self.call(["add", filename])

    def tag(self, name, message):
        self.call(["tag", name, "-m", message])

    # Returns the SHA1 checksum as a bytes object without trailing newline!
    def getSHA1(self, ref):
        p = Popen(["git", "show-ref", "-s", ref], stdout=PIPE)
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

    # TODO maybe name "run", because of "runSubpatch"
    def call(self, args):
        call(["git"] + args)

    def diff_staged_files(self):
        # TODO use '\0' delimeter instead of '\n'
        p = Popen(["git", "diff", "--name-status", "--staged"], stdout=PIPE)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("error here")

        return stdout.rstrip(b"\n").split(b"\n")


def touch(filename, file_content):
    with open(filename, "bw") as f:
        f.write(file_content)


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
        cls.tmpdir = tempfile.mkdtemp(prefix=cls.__name__,
                                      dir=os.path.dirname(__file__))
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
                sys.stdout.buffer.write(content_actual)
                sys.stdout.buffer.flush()

            self.assertEqual(content_actual, content_expected)


@contextlib.contextmanager
def cwd(path, create=False):
    if create:
        mkdir(path)
    old_path = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_path)
