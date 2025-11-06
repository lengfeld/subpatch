#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import sys
import unittest
from os import mkdir
from os.path import dirname, join, realpath
from helpers import (TestCaseTempFolder, TestCaseHelper, create_and_chdir, Git,
                     create_git_repo_with_branches_and_tags)

path = realpath(__file__)
sys.path.append(join(dirname(path), "../src"))

from cache import CacheHelperGit, DownloadConfig


# TODO Add tests for all different Cache Helpers types

class TestCacheHelperGit(TestCaseTempFolder, TestCaseHelper):
    def test_create(self):
        cache_helper = CacheHelperGit()
        cwd_to_cache_relpath = b"cache"
        mkdir(cwd_to_cache_relpath)
        self.assertFalse(cache_helper.isCreated(cwd_to_cache_relpath))
        cache_helper.create(cwd_to_cache_relpath)
        self.assertTrue(cache_helper.isCreated(cwd_to_cache_relpath))

    def test_fetch(self):
        with create_and_chdir("upstream"):
            create_git_repo_with_branches_and_tags()
            git = Git()
            head_id = git.get_sha1("HEAD")
            tag_id = git.get_sha1("v1")
            tag_commit_id = git.get_sha1("v1^{commit}")

        cache_helper = CacheHelperGit()
        cwd_to_cache_relpath = b"cache"
        mkdir(cwd_to_cache_relpath)
        cache_helper.create(cwd_to_cache_relpath)

        download_config = DownloadConfig("upstream", "main")
        object_id = cache_helper.fetch(cwd_to_cache_relpath, download_config)
        self.assertEqual(object_id, head_id)

        download_config = DownloadConfig("upstream", "v1")
        object_id = cache_helper.fetch(cwd_to_cache_relpath, download_config)
        self.assertEqual(object_id, tag_id)

        download_config = DownloadConfig(url="upstream")
        object_id = cache_helper.fetch(cwd_to_cache_relpath, download_config)
        self.assertEqual(object_id, head_id)

        # TODO Document and find out the correct path for relative local paths
        download_config = DownloadConfig(url="upstream")
        object_id = cache_helper.fetch(cwd_to_cache_relpath, download_config)
        self.assertEqual(object_id, head_id)

        download_config = DownloadConfig(url="upstream", revision=tag_commit_id.decode("ascii"))
        object_id = cache_helper.fetch(cwd_to_cache_relpath, download_config)
        self.assertEqual(object_id, tag_commit_id)


if __name__ == '__main__':
    unittest.main()
