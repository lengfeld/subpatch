#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import unittest
from os.path import dirname, join, realpath

from helpers import TestCaseTempFolder

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))


# TODO Add tests for all different Cache Helpers types
class TestCache(TestCaseTempFolder):
    def test_something(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
