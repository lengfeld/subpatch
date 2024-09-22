#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import tempfile
import unittest
import shutil
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

    def commit(self, msg):
        self.call(["commit", "-m", "msg", "-q"])

    # TODO maybe name "run", because of "runSubpatch"
    def call(self, args):
        call(["git"] + args)

    # TODO what is the member function naming convention?
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


@contextlib.contextmanager
def cwd(cwd):
    old_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(old_cwd)
