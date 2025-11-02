#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import unittest
from os.path import dirname, join, realpath

path = realpath(__file__)
sys.path.append(join(dirname(path), "../"))

from src.libconfig import (ConfigLine, LineDataEmpty, LineDataHeader,
                           LineDataKeyValue, LineType, config_add_section2,
                           config_drop_key2, config_drop_section_if_empty,
                           config_parse2, config_set_key_value2, config_unparse2,
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
        self.compare(b"section", b"""\
[section]
""", b"""\
""")

    def test_simple_no_drop(self):
        self.compare(b"section", b"""\
[section]
\tkey = value
""", b"""\
[section]
\tkey = value
""")

    def test_complex(self):
        self.compare(b"a", b"""\
[a]
[b]
[c]
""", b"""\
[b]
[c]
""")
        self.compare(b"b", b"""\
[a]
[b]
[c]
""", b"""\
[a]
[c]
""")
        self.compare(b"c", b"""\
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


if __name__ == '__main__':
    unittest.main()
