#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import os
import tempfile
import unittest
import shutil
import contextlib
from os.path import isfile, isdir, join, realpath, dirname


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
