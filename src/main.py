#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import argparse
import os
import shutil
import subprocess
import sys
import time
from contextlib import chdir
from dataclasses import dataclass
from os.path import join
from subprocess import DEVNULL, Popen

# ----8<----
from cache import CacheHelperGit, DownloadConfig
from libconfig import (LineDataHeader, LineDataKeyValue, LineType,
                       config_add_section2, config_drop_key2,
                       config_drop_section_if_empty, config_parse2,
                       config_set_key_value2, config_unparse2, empty_config_lines,
                       split_with_ts_bytes)
# TODO main.py should not depend on any git command. They all should be in cache.py
# or in a new super.py module
from libgit import (get_name_from_repository_url, git_diff_in_dir,
                    git_diff_name_only, git_ls_files_untracked, is_valid_revision,
                    git_ls_files)
from util import AppException, ErrorCode, URLTypes, get_url_type
from super import (find_superproject, SCMType, check_superproject_data,
                   check_and_get_superproject_from_checked_data, SuperprojectType,
                   SuperHelperGit, Superproject, SuperHelper)

# ----8<----

# See https://peps.python.org/pep-0440/ for details about the version format.
# e.g. dashes "-" are not allowed and 'a' stands for 'alpha' release.
__version__ = "0.1a6"

# It's the SPDX identifier. See https://spdx.org/licenses/GPL-2.0-only.html
__LICENSE__ = "GPL-2.0-only"


# "Section names are case-insensitive. Only alphanumeric characters, - and .
# are allowed in section names"
def is_section_name(b):
    raise NotImplementedError()


@dataclass(frozen=True)
class Config:
    subprojects: list[bytes]


def parse_config(config_lines) -> Config:
    subprojects = []

    in_subprojects = False
    for config_line in config_lines:
        line_data = config_line.line_data
        if config_line.line_type == LineType.HEADER:
            assert isinstance(line_data, LineDataHeader)
            if line_data.section_name == b"subprojects" and line_data.subsection_name is None:
                in_subprojects = True
            else:
                in_subprojects = True
        elif config_line.line_type == LineType.KEY_VALUE:
            assert isinstance(line_data, LineDataKeyValue)
            if in_subprojects:
                if line_data.key == b"path":
                    subprojects.append(line_data.value)
        else:
            pass

    return Config(subprojects)


# Path can be absolute or relative
def read_config(path: bytes) -> Config:
    with open(path, "br") as f:
        config_lines = config_parse2(split_with_ts_bytes(f.read()))

    return parse_config(config_lines)


# Paths documentation and naming
#
#     Example              ../folder/superproject/dirA/dirB/subproject/
#                                                 ^^^^cwd
#
#     super_abspath:       ../folder/superproject
#       other name: "top level directory" TODO unify
#     config_abspath:      ../folder/superproject/.subpatch
#     super_to_sub_relpath:                       dirA/dirB/subproject
#     super_to_cwd_relpath:                       dirA
#     cwd_to_sub_relpath:                              dirB/subproject
#     sub_name:                                             subproject
#
#     TODO finalized this naming
#     Note on path/filesystem nameing
#      - path: "dir/test", "/dir/test"
#      - file: a file in a filesystem!
#      - filename: can be a dir name or a regular file name
#     reduandent words:
#      - maybe pathname
#      - maybe dirname
#
# TODO test and fix all the edge cases
#  e.g. cwd_to_sub_relpath="../symbolic-link/../../dir"
#  - symbolic links
#  - ".." pointing outside of repo
@dataclass(frozen=True)
class SuperPaths:
    super_abspath: bytes
    config_abspath: bytes  # TODO Maybe just have a single abspath in super_abspath
    super_to_cwd_relpath: bytes


# TODO is it "<object>_<verb>" or "<verb>_<object>"?
#  "subprojects_parse" vs "parse_subprojects"
#  ... -> then should should be "parse_config_parts_to_subprojects

@dataclass(frozen=True)
class SubPaths:
    super_to_sub_relpath: bytes
    cwd_to_sub_relpath: bytes  # Can be ".." or "../.." if cwd is inside a subproject
    sub_name: bytes  # Can be b"" when subproject is at the toplevel directory (but this is not supported for now)
    subproject_abspath: bytes
    metadata_abspath: bytes  # Path to ".subproject" file
    patches_abspath: bytes  # Path to "patches" directory


def gen_sub_paths_from_relpath(super_paths: SuperPaths, super_to_sub_relpath: bytes) -> SubPaths:
    # Returns a relative paht from the current work directory
    cwd_to_sub_relpath = os.path.relpath(join(super_paths.super_abspath, super_to_sub_relpath))
    if cwd_to_sub_relpath == b".":
        cwd_to_sub_relpath = b""

    return gen_sub_paths_internal(super_paths, super_to_sub_relpath, cwd_to_sub_relpath)


def gen_sub_paths_from_cwd_and_relpath(super_paths: SuperPaths, cwd_to_sub_relpath: bytes) -> SubPaths:
    # Sanitize input path
    if cwd_to_sub_relpath != b"":
        cwd_to_sub_relpath = os.path.relpath(cwd_to_sub_relpath)
        if cwd_to_sub_relpath == b".":
            cwd_to_sub_relpath = b""

    super_to_sub_relpath = join(super_paths.super_to_cwd_relpath, cwd_to_sub_relpath)

    return gen_sub_paths_internal(super_paths, super_to_sub_relpath, cwd_to_sub_relpath)


def gen_sub_paths_internal(super_paths: SuperPaths, super_to_sub_relpath: bytes, cwd_to_sub_relpath: bytes) -> SubPaths:
    # Remove trailing slash if there is any
    # TODO is this correct? Does this makes sense?
    if super_paths.super_to_cwd_relpath != b"":
        super_to_sub_relpath = os.path.relpath(super_to_sub_relpath)

    def my_join(a, b):
        if a == b"":
            return b
        if b == b"":
            return a
        # If b contains ".." or "../..", strip path components, instead of
        # adding ".."
        return os.path.relpath(join(a, b))

    assert super_to_sub_relpath == my_join(super_paths.super_to_cwd_relpath, cwd_to_sub_relpath)

    sub_name = os.path.basename(super_to_sub_relpath)

    subproject_abspath = join(super_paths.super_abspath, super_to_sub_relpath)

    metadata_abspath = join(subproject_abspath, b".subproject")

    patches_abspath = join(subproject_abspath, b"patches")

    return SubPaths(super_to_sub_relpath, cwd_to_sub_relpath, sub_name, subproject_abspath, metadata_abspath, patches_abspath)


@dataclass(frozen=True)
class Metadata:
    # TODO introduce seperation between sections (subtree, upstream, patches)
    # TODO introduce boolean values whether header/sections exists. This can be
    # a different case then the value exists.
    url: bytes | None
    revision: bytes | None
    object_id: bytes | None
    subtree_applied_index: bytes | None
    subtree_checksum: bytes | None


def read_metadata(path: bytes) -> Metadata:
    try:
        with open(path, "br") as f:
            lines = split_with_ts_bytes(f.read())
    except FileNotFoundError:
        # TODO add note about which subproject is wrong!
        # TODO write commands to fix this issue.
        # NOTE This state cannot/should not arise when subpatch commands are used.
        raise AppException(ErrorCode.INVALID_STATE, "Metadata file for subproject not found."
                           " Drop subproject path from the subpatch config or add a subproject metadata file manually!.")

    url = None
    revision = None
    object_id = None
    subtree_applied_index = None
    subtree_checksum = None

    metadata_lines = config_parse2(lines)
    for metadata_line in metadata_lines:
        # TODO only use url and revision in upstream section!
        if metadata_line.line_type == LineType.KEY_VALUE:
            line_data = metadata_line.line_data
            assert isinstance(line_data, LineDataKeyValue)
            if line_data.key == b"url":
                url = line_data.value
            elif line_data.key == b"revision":
                revision = line_data.value
            elif line_data.key == b"objectId":
                object_id = line_data.value
            elif line_data.key == b"appliedIndex":
                subtree_applied_index = line_data.value
            elif line_data.key == b"checksum":
                subtree_checksum = line_data.value

    return Metadata(url, revision, object_id, subtree_applied_index, subtree_checksum)


# Data class that contains most of the information that is in the subtree
# dimension of a subproject. The actuall files in the subtree are left out!
@dataclass(frozen=True)
class SubtreeDim:
    # Range: -1 <= applied_index < len(patches)
    # - -1 := no applied patch
    # -  0 := first patch applied,
    # -  1 := second patch applied,
    #   ...
    # The default value is None for "all tracked patches are applied"
    applied_index: int | None
    # TODO Use SHA1 Checksum type instead of 'bytes'
    checksum: bytes   # Default value is b"", which means that the subtree is unpopulated


# TODO prefix "read" is wrong. It's correct for "read_metadata", but here nothing is read from disk!
def read_subtree_dim(metadata: Metadata) -> SubtreeDim:
    if metadata.subtree_applied_index is not None:
        # TODO add error when value is not an int!
        applied_index = int(metadata.subtree_applied_index)
    else:
        applied_index = None

    if metadata.subtree_checksum is None:
        checksum = b""  # Use default value
    else:
        # TODO Check checksum that it's a valid SHA1 sum
        checksum = metadata.subtree_checksum

    return SubtreeDim(applied_index, checksum)


# Data class that contains most of the information that is in the patches
# dimension of a subproject.
@dataclass(frozen=True)
class PatchesDim:
    patches: list[bytes]


def read_patches_dim(sub_paths: SubPaths, metadata: Metadata) -> PatchesDim:
    try:
        patches = os.listdir(sub_paths.patches_abspath)
        patches = [p for p in patches if p.endswith(b".patch")]
        patches.sort()
    except FileNotFoundError:
        patches = []

    return PatchesDim(patches)


def ensure_dims_are_consistent(subtree_dim: SubtreeDim, patches_dim: PatchesDim) -> None:
    if subtree_dim.applied_index is not None:
        if subtree_dim.applied_index < -1:
            raise AppException(ErrorCode.INVALID_STATE,
                               "Value of appliedIndex is smaller than -1. Metadata is inconsistent!")
        if subtree_dim.applied_index >= len(patches_dim.patches):
            raise AppException(ErrorCode.INVALID_STATE,
                               "Value of appliedIndex is bigger than the count of patches. Metadata is inconsistent!")


def nocommand(args, parser) -> int:
    parser.print_help(file=sys.stderr)
    return 2  # TODO why 2?


def cmd_help(args, parser) -> int:
    parser.print_help()
    return 0


# TODO clarify naming: path, filename, url
# TODO clairfy name for remote git name and path/url

# Naming:
# Variable names:
#  - url: The URL for a git/svn/.. repository or tarball.
#      Can be a http, git or file URL. Or just a local path.
#    Variant:
#       url: The subproject's URL, e.g. to clone/download
#
# subpatch naming
#  - "config" or "subpatch config". Is the name of the config in the
#    ".subpatch" file at the toplevel of the superproject.
#    TODO add to glossary
#  - "subproject": Idea: Is only the local directory and config
#                  Not the remote repository


def ensure_superproject_is_configured(superx):
    # Design decision:
    # Having a empty ".subpatch" config file is something different than having
    # no config file. It means that subptach is not yet configured for the project.
    # TODO document this design decision somewhere else!
    if not superx.configured:
        raise AppException(ErrorCode.SUPERPROJECT_NOT_CONFIGURED)


def ensure_superproject_is_git(superx):
    if superx.typex != SuperprojectType.GIT:
        raise AppException(ErrorCode.NOT_IMPLEMENTED_YET, "This feature currently works only in a git superproject!")


# TODO consolidate with unpack from cmd_add
# TODO consolide function arguments
def do_unpack_for_update(superx, super_paths, sub_paths, cache_abspath: bytes, url: str, revision: str | None, object_id: bytes) -> None:
    # TODO This function is very very hacky. Works for now!

    # Quick and dirty performance improvement. Batch multiple paths together
    class GitCommandBachter:
        BATCH_COUNT = 5000

        def __init__(self, cmd):
            self._args = []
            self._cmd = cmd

        def add_and_maybe_exec(self, arg):
            self._args.append(arg)
            if len(self._args) >= self.BATCH_COUNT:
                self.exec_force()

        # NOTE: This function is cwd aware!
        def exec_force(self):
            if len(self._args) == 0:
                return
            cmd = self._cmd + self._args
            subprocess.run(cmd, check=True)
            self._args.clear()

    # Just quick and try remove and copy!
    # TODO convert this code to "superhelper" implementation
    # TODO This code is "subpatch subtree drop"
    with chdir(super_paths.super_abspath):
        # TODO ensure that there are no untracked changes. Subpatch should not
        # remove any work of the user by accident.
        git_rm = GitCommandBachter(["git", "rm", "-q", "-f"])
        # TODO Add a custom/plumping command for that "subpatch subtree list"
        with chdir(sub_paths.super_to_sub_relpath):
            subtree_files_relpaths = git_ls_files()
            # NOTE: git_ls_tree_in_dir() also lists files non-subtree files E.g.
            # the folder "patches" and the file ".subproject". These must be
            # skipped.
            for path in subtree_files_relpaths:
                if path.startswith(b"patches/"):
                    continue
                if path == b".subproject":
                    continue
                git_rm.add_and_maybe_exec(path)
            git_rm.exec_force()

    # and copy

    # TODO This code is "subpatch unpack" but even bit lower
    # TODO convert this code to "superhelper" implementation
    os.makedirs(sub_paths.cwd_to_sub_relpath, exist_ok=True)
    with chdir(cache_abspath):
        git_add = GitCommandBachter(["git", "add", "-f"])

        for root, dirnames, files in os.walk(b"."):
            for dirname in dirnames:
                super_to_dest_relpath = join(sub_paths.super_to_sub_relpath, root, dirname)
                dest_path = join(super_paths.super_abspath, super_to_dest_relpath)
                os.makedirs(dest_path, exist_ok=True)

            for filename in files:
                src_path = join(root, filename)
                super_to_dest_relpath = join(sub_paths.super_to_sub_relpath, root, filename)
                dest_path = join(super_paths.super_abspath, super_to_dest_relpath)
                os.rename(src_path, dest_path)
                super_to_dest_relpath = join(sub_paths.super_to_sub_relpath, root, filename)

                git_add.add_and_maybe_exec(super_to_dest_relpath)

        with chdir(super_paths.super_abspath):
            git_add.exec_force()

    # Remove empty directories in download/cache dir
    for root, dirnames, files in os.walk(cache_abspath, topdown=False):
        assert len(files) == 0
        for dirname in dirnames:
            os.rmdir(join(root, dirname))

    assert len(os.listdir(cache_abspath)) == 0
    os.rmdir(cache_abspath)

    with chdir(super_paths.super_abspath):
        subtree_checksum = superx.helper.get_sha1_for_subtree(sub_paths.super_to_sub_relpath)

    metadata_set_for_unpack(sub_paths, url, revision, object_id, subtree_checksum)

    with chdir(super_paths.super_abspath):
        superx.helper.add([sub_paths.metadata_abspath])


def cmd_update(args, parser):
    if args.path is None:
        # TODO should also work when cwd is inside the subproject
        raise AppException(ErrorCode.NOT_IMPLEMENTED_YET, "Must give path to subproject")

    data = find_superproject()
    checked_data = check_superproject_data(data)
    superx = check_and_get_superproject_from_checked_data(checked_data)
    ensure_superproject_is_configured(superx)
    ensure_superproject_is_git(superx)
    cwd_to_sub_relpath = os.fsencode(args.path)

    super_paths = gen_super_paths(superx.path)
    sub_paths = gen_sub_paths_from_cwd_and_relpath(super_paths, cwd_to_sub_relpath)

    # TODO Hardcoded assumption: subproject is also git
    cache_helper = CacheHelperGit()

    config = read_config(super_paths.config_abspath)

    # NOTE two different error cases:
    # * no subproject path in config
    # * no subproject file in directory (TODO add code for that)
    # TODO make this check generic!
    if sub_paths.super_to_sub_relpath not in config.subprojects:
        x = sub_paths.super_to_sub_relpath.decode("utf8")
        raise AppException(ErrorCode.INVALID_ARGUMENT, "Path '%s' does not point to a subproject" % (x,))

    metadata = read_metadata(sub_paths.metadata_abspath)

    if args.url is not None:
        # TODO verify URL
        url = args.url
    else:
        if metadata.url is None:
            # TODO this is an error case. There should always be an URL
            # TODO but actually this might depend on the Cache/SubHelper. Maybe
            # there is an implementetion that does not need a URL.  Or maybe the
            # field should be mandertory.
            url = None
        else:
            url = metadata.url.decode("utf8")

    if args.revision is not None:
        # TODO verify revision
        revision = args.revision
    else:
        if metadata.revision is None:
            revision = None
        else:
            revision = metadata.revision.decode("utf8")

    assert isinstance(url, str)
    assert revision is None or isinstance(revision, str)

    # NOTE staged changes in the subtree of the subproject are ok. We assume that the
    # subproject is in a clean/sane state. E.g. the user has deapplyed some or all patches.
    # Untrack changes are _not_ ok. It's mostly means that the subproject is not clean.
    if git_diff_in_dir(superx.path, sub_paths.super_to_sub_relpath):
        # TODO add more explanations and commands to fix!
        raise AppException(ErrorCode.INVALID_ARGUMENT, "There are unstaged changes in the subproject.")

    # TODO check that the subproject is in a clean state

    # For now check whether all patches are deapplied!
    patches_dim = read_patches_dim(sub_paths, metadata)
    subtree_dim = read_subtree_dim(metadata)
    ensure_dims_are_consistent(subtree_dim, patches_dim)

    if len(patches_dim.patches) > 0:
        # TODO refactor common code with cmd_pop,push
        if subtree_dim.applied_index is None:
            applied_index = len(patches_dim.patches) - 1
        else:
            applied_index = subtree_dim.applied_index
        if applied_index != -1:
            # TODO also check for linting issue, when default value is used!
            raise AppException(ErrorCode.NOT_IMPLEMENTED_YET, "subproject has patches applied. Please pop first!")

    # TODO deapply all patches

    if not args.quiet:
        # TODO printing is not correct. In case of an error, the newline is not
        # printed!
        print("Updating subproject '%s' from URL '%s' to revision '%s'..." %
              (sub_paths.cwd_to_sub_relpath.decode("utf8"), url, cache_helper.get_revision_as_str(revision)),
              end="")
        sys.stdout.flush()

    # subpatch download

    # TODO if git, and revision is a commit or tag id, check that the new sha1/id
    # is the same as the already integrated (not yet saved to config). If they are
    # the same, no need to reintegrated!
    # - Note: if there are subtree or exclude changes, update must still be done!

    # TODO implement git dir optimization
    # - use a bare repository! And ad-hoc checkouts
    # - And at best do not checkout, just import the git objects into the
    # current git and let git of the superproject check it out.
    cache_relpath = sub_paths.cwd_to_sub_relpath + b"-tmp"

    # TODO optimize with ls-remote, If the commit/tag hash are equal, don't
    # download!

    download_config = DownloadConfig(url=url, revision=revision)
    # Fetch remote repository/tarball into local folder and checkout the
    # requested revision.
    # NOTE: The ".git" folder is already removed! Just the plain tree
    object_id = cache_helper.download(download_config, cache_relpath)

    cache_abspath = os.path.abspath(join(os.getcwdb(), cache_relpath))

    # subpatch unpack
    try:
        do_unpack_for_update(superx, super_paths, sub_paths, cache_abspath, url, revision, object_id)
    except Exception:
        # TODO maybe some other layer of subpatch should be responsible for the
        # cleanup.
        if os.path.exists(cache_abspath):
            print("Warning: Cache directory '{cache_relpath}' still exists. Removing it!", file=sys.stderr)
            # TODO rmtree is always a bit risky. subpatch should not remove
            # random files from the user.
            shutil.rmtree(cache_abspath)

    # TODO reapply patches: subpatch push --all
    # TODO only apply to the same index as before, not just all patches!

    if not args.quiet:
        print(" Done.")

    # TODO Think about the case when there are no changes in the subproject. Or
    # just no changes in the subtree. (e.g. just a rev/object_id update). Maybe
    # the user wants to know that. So maybe subpatch should have a exit code
    # for that.

    if not args.quiet:
        # TODO Idea "subpatch status" should print the info/help text. The status
        # command should be command to get help if a user is lost.
        superx.helper.print_instructions_to_commit_and_inspect()

    return 0


# Argument config can be relpath or an abspath
# TODO use other prefix "config_" for parser! prefix "config" is for the
# subpatch config file.
def config_add_subproject(config_path: bytes, super_to_sub_relpath: bytes) -> None:
    try:
        # TODO read as bytes instead of str type
        with open(config_path, "br") as f:
            config_lines = config_parse2(split_with_ts_bytes(f.read()))
    except FileNotFoundError:
        config_lines = empty_config_lines()

    config_lines = config_add_section2(config_lines, b"subprojects")
    config_lines = config_set_key_value2(config_lines, b"subprojects", b"path", super_to_sub_relpath, append=True)

    with open(config_path, "bw") as f:
        # TODO parse and unparse are _not_ symmetric. Fix this
        f.write(config_unparse2(config_lines))


def do_unpack_for_add(superx, super_paths, sub_paths, cache_relpath: bytes, url: str, revision: str | None, object_id: bytes) -> None:
    # HACK for now
    # Check assumptions: We have just created the files ourselves
    assert os.path.exists(sub_paths.cwd_to_sub_relpath)
    assert os.path.exists(sub_paths.metadata_abspath)
    # TODO always check that for subprojects
    assert not os.path.exists(join(cache_relpath, b".subproject"))
    os.remove(sub_paths.metadata_abspath)
    os.rmdir(sub_paths.cwd_to_sub_relpath)
    os.rename(cache_relpath, sub_paths.cwd_to_sub_relpath)

    superx.helper.add([sub_paths.cwd_to_sub_relpath])

    # Hack for now:
    # The funciton get_sha1_for_subtree does not work if the subtree is empty
    # (=no files tracked by git in it). So just create and add a file for the moment.
    # This case only happens, when the upstream projet has a empty file tree. This is
    # also a rare case. Someone would say this would be even a error case ;-)
    # TODO add argument to allow empty subtrees in the upstream repo.
    with open(sub_paths.metadata_abspath, "bw"):
        pass
    with chdir(super_paths.super_abspath):
        superx.helper.add([sub_paths.metadata_abspath])

    # TODO in case of failure, remove download git dir!
    with chdir(super_paths.super_abspath):
        subtree_checksum = superx.helper.get_sha1_for_subtree(sub_paths.super_to_sub_relpath)

    metadata_set_for_unpack(sub_paths, url, revision, object_id, subtree_checksum)

    with chdir(super_paths.super_abspath):
        superx.helper.add([sub_paths.metadata_abspath])


# Consolide into plumping commands
#   subpatch configure (--auto)
#   subpatch init <subproject path>
#   subpatch subtree clean --check # tricky, cannot be really done before or must he handcoded!
#   subpatch download
#     - subpatch cache init --type=git   # --autoremove'
#     - subpatch fetch <url> -r <rev>
#   subpatch unpack   # honors "--autoremove"
#     - does cp/mv
#     - subpatch subtree checksum write"
#     - subpatch upstream add url -r <rev> -o <id>
def cmd_add(args, parser):
    if args.url is None:
        # TODO make error message nicer
        raise Exception("Not the correct amount of args")

    if args.path is not None:
        # The optional path argument was given. Make some checks
        if len(args.path) == 0:
            raise AppException(ErrorCode.INVALID_ARGUMENT, "path is empty")
        # TODO But something like "/./././" is also invalid"
        # TODO disallow absolute paths
        # TODO think about relative paths, whether the must be relative to the
        # remote origin url! Repo and git-submodule do that

    revision: str | None = args.revision
    url = args.url

    if revision is not None:
        if not is_valid_revision(revision):
            # TODO add reason why it's invalid
            raise AppException(ErrorCode.INVALID_ARGUMENT, "revision '%s' is invalid" % (revision,))

    # TODO check with ls-remote that remote is accessible

    if args.path is None:
        cwd_to_sub_relpath = get_name_from_repository_url(url)
    else:
        cwd_to_sub_relpath = args.path
        # TODO split into path and name component
        # sanitize path. Remove double slashes trailing slash
        # and paths that are outside of the repository
        # - For now just remove trailing slashes
        # TODO same checks are needed for `cmd_init`
        cwd_to_sub_relpath = cwd_to_sub_relpath.rstrip("/")

    url_type = get_url_type(url)

    data = find_superproject()
    checked_data = check_superproject_data(data)
    superx = check_and_get_superproject_from_checked_data(checked_data)
    ensure_superproject_is_git(superx)

    super_paths = gen_super_paths(superx.path)

    # TODO remove additional encode() here.
    sub_paths = gen_sub_paths_from_cwd_and_relpath(super_paths, cwd_to_sub_relpath.encode("utf8"))

    if url_type == URLTypes.LOCAL_RELATIVE:
        # Check the current work directory of the call is the top level
        # directory of the repository. If not, a relative path on the
        # command line is not relative to the top level directory and must be
        # converted. This conversion is a bit complex and error prone.  So
        # just enforce (like also git does) that the current work directory
        # is the top level repository in that case.
        # TODO This is a invalid argument execption
        if not is_cwd_toplevel_directory(super_paths):
            raise AppException(ErrorCode.CUSTOM,
                               "When using relative repository URLs, you current work directory "
                               "must be the toplevel folder of the superproject!")
    elif url_type == URLTypes.LOCAL_ABSOLUTE:
        # TODO add reason why it's not supported
        raise AppException(ErrorCode.CUSTOM, "Absolute local paths to a remote repository are not supported!")

    # TODO check that git repo has nothing in the index!
    # But some changes are ok:
    # TODO add tests that adds a subproject after a "git rm -r" to the same folder.
    # So the changes are in the filesystem and in the index, but not committed yet.
    # This should work

    # subpatch configure
    if not superx.configured:
        do_configure(superx.path, superx.helper)

    # NOTE: At this point subpatch is using the git staging area as a
    # rollback/revert mechansim. If something fails in the next code lines,
    # the user (and the tests) can revert with "git revert".
    # TODO maybe make this built-in!
    # TODO add notes how to revert if anything of the following fails!

    # subpatch init <path>
    do_init(super_paths, sub_paths, superx)

    # subpatch cache init --git
    cache_helper = CacheHelperGit()
    # TODO split into directory and cache_name
    cache_relpath = sub_paths.cwd_to_sub_relpath + b"-tmp"

    # NOTE: Design decision: The output is relative to the current working dir.
    # The content of '%s' is the remote git name or the path relative to the
    # current working dir. It's not relative to the top level dir of the git repo.
    # TODO move this design decision to the website
    if not args.quiet:
        print("Adding subproject '%s' from URL '%s' at revision '%s'..." %
              (sub_paths.cwd_to_sub_relpath.decode("utf8"), url, cache_helper.get_revision_as_str(revision)),
              end="")
        sys.stdout.flush()

    try:
        # subpatch cache fetch url -r version
        download_config = DownloadConfig(url=url, revision=revision)

        # Fetch remote repository/tarball into local folder and checkout the
        # requested revision.
        object_id = cache_helper.download(download_config, cache_relpath)

        # subpatch unpack # from cache into woktree
        do_unpack_for_add(superx, super_paths, sub_paths, cache_relpath, url, revision, object_id)
    except Exception as e:
        # If there is any exception, still print the final new line character.
        # Otherwise the error message that is printed is not beginning at the
        # start of the line.
        if not args.quiet:
            print(" Failed.")
            sys.stdout.flush()
        raise e
    else:
        if not args.quiet:
            print(" Done.")
            # TODO is flush() also needed here?

    # TODO Idea "subpatch status" should print the info/help text. The status
    # command should be command to get help if a user is lost.
    if not args.quiet:
        superx.helper.print_instructions_to_commit_and_inspect()

    # TODO Maybe prepare a commit/patch/change message

    return 0


def show_version(args) -> int:
    print("subpatch version %s" % (__version__,))
    return 0


def show_info(args) -> int:
    print("homepage:  https://subpatch.net")
    print("git repo:  https://github.com/lengfeld/subpatch")
    print("license:   %s" % (__LICENSE__,))
    # TODO add GPL license text/note
    return 0


def do_configure(super_abspath: bytes, super_helper: SuperHelper) -> None:
    config_abspath = join(super_abspath, b".subpatch")
    assert not os.path.exists(config_abspath)
    with open(config_abspath, "bw"):
        pass

    with chdir(super_abspath):
        super_helper.add([b".subpatch"])


# TODO implement option to unconfigure a superproject
# TODO unconfiguring should only be possible if all subprojects are removed!
def cmd_configure(args, parser):
    data = find_superproject()
    checked_data = check_superproject_data(data)

    if checked_data is None:
        # There is no config file and no SCM
        # TODO implement with "subpatch configure --here"
        raise AppException(ErrorCode.NOT_IMPLEMENTED_YET,
                           "No SCM found. Cannot configure. '--here' not implemented yet!")
    elif checked_data.configured:
        # Nothing to do, the superproject is already configured.
        if not args.quiet:
            print("The file .subpatch already exists. Nothing to do!")
    else:
        # There is no ".subpatch" file (=the superproject is not configured)

        # TODO Use check_and_get_superproject_from_checked_data to get rid of
        # SCMType.GIT here in main.py
        if checked_data.scm_type == SCMType.GIT:
            # TODO see above. Use other function to switch between super implementations.
            super_helper = SuperHelperGit()

            do_configure(checked_data.super_path, super_helper)

            if not args.quiet:
                super_helper.print_configure_success()
        else:
            # Unsupported SCMType
            raise AppException(ErrorCode.NOT_IMPLEMENTED_YET,
                               "SCM not supported. Currently subpatch only supports git")

    return 0


# TODO Document own internal path library
#  - e.g. b"" is the same as b"." and the later is not used!
# TODO add tests
def is_relpath(path):
    if len(path) == 0:
        return True
    if path[0] == ord("/"):
        return False
    return True


# NOTE: It's the inverse of is_relpath()
# TODO add tests
def is_abspath(path):
    if len(path) == 0:
        return False
    if path[0] != ord("/"):
        return False
    return True


def gen_super_paths(super_abspath: bytes) -> SuperPaths:
    assert is_abspath(super_abspath)

    cwd_abspath = os.path.abspath(os.getcwdb())
    assert cwd_abspath.startswith(super_abspath)
    super_to_cwd_relpath = cwd_abspath[len(super_abspath) + 1:]

    config_abspath = join(super_abspath, b".subpatch")

    return SuperPaths(super_abspath, config_abspath, super_to_cwd_relpath)


def is_inside_subproject_and_return_path(config: Config, super_paths: SuperPaths) -> bytes | None:
    # This algorithm was too simple. E.g the paths
    #   ["subproject", "subproject-second"]
    # with cwd "subproject/subdir", was not recognized correctly.
    # Now the algorithm does not make a string compare, it converts the paths
    # to list and compare the list entries.
    super_to_cwd_relpath_parts = super_paths.super_to_cwd_relpath.split(b"/")
    for relpath in config.subprojects:
        # TODO assert that relpath is sane!
        # TODO introduce naming convention. How are the parts of a path called?
        # "parts", "path components" or "filenames"?
        relpath_parts = relpath.split(b"/")
        amount_of_same_components = min(len(relpath_parts), len(super_to_cwd_relpath_parts))
        if relpath_parts[:amount_of_same_components] == super_to_cwd_relpath_parts[:amount_of_same_components]:
            return relpath
    return None


# TODO currently this always uses "\t" for indention. Try to use the style
# that is already used in the subpatch file. E.g. four-spaces, two-spaces
# or no-spaces.
# NOTE: DDX/Design decision: The URL is taken as a verbatim copy
# of the argument. If there is a trailing slash in the argument, then the
# trailing slash is also in the config file. It's not sanitized. It's the
# same behavior as 'git submodule' does.
def metadata_set_for_unpack(sub_paths: SubPaths, url: str, revision: str | None, object_id: bytes,
                            subtree_checksum: bytes | None = None) -> None:
    try:
        with open(sub_paths.metadata_abspath, "br") as f:
            metadata_lines = config_parse2(split_with_ts_bytes(f.read()))
    except FileNotFoundError:
        metadata_lines = empty_config_lines()

    metadata_lines = config_add_section2(metadata_lines, b"upstream")
    metadata_lines = config_set_key_value2(metadata_lines, b"upstream", b"url", url.encode("utf8"))
    if revision is not None:
        metadata_lines = config_set_key_value2(metadata_lines, b"upstream", b"revision", revision.encode("utf8"))
    if subtree_checksum is not None:
        metadata_lines = config_add_section2(metadata_lines, b"subtree")
        metadata_lines = config_set_key_value2(metadata_lines, b"subtree", b"checksum", subtree_checksum)
    metadata_lines = config_set_key_value2(metadata_lines, b"upstream", b"objectId", object_id)

    metadata_config = config_unparse2(metadata_lines)
    with open(sub_paths.metadata_abspath, "bw") as f:
        f.write(metadata_config)


# TODO maybe use metadata_abspath instead of SubPaths
# TODO Mabye this "metadata_*" is the new naming convention with verbs "set", "drop"
def metadata_set_applied_index(sub_paths: SubPaths, applied_index: int) -> None:
    try:
        with open(sub_paths.metadata_abspath, "br") as f:
            metadata_lines = config_parse2(split_with_ts_bytes(f.read()))
    except FileNotFoundError:
        metadata_lines = empty_config_lines()

    metadata_lines = config_add_section2(metadata_lines, b"subtree")
    metadata_lines = config_set_key_value2(metadata_lines, b"subtree", b"appliedIndex", b"%d" % (applied_index,))

    metadata_config = config_unparse2(metadata_lines)
    with open(sub_paths.metadata_abspath, "bw") as f:
        f.write(metadata_config)


# TODO maybe use metadata_abspath instead of SubPaths
# TODO refactor with other update commands
def metadata_set_subtree_checksum(sub_paths: SubPaths, subtree_checksum: bytes) -> None:
    try:
        with open(sub_paths.metadata_abspath, "br") as f:
            metadata_lines = config_parse2(split_with_ts_bytes(f.read()))
    except FileNotFoundError:
        metadata_lines = empty_config_lines()

    metadata_lines = config_add_section2(metadata_lines, b"subtree")
    metadata_lines = config_set_key_value2(metadata_lines, b"subtree", b"checksum", subtree_checksum)

    metadata_config = config_unparse2(metadata_lines)
    with open(sub_paths.metadata_abspath, "bw") as f:
        f.write(metadata_config)


# TODO maybe use metadata_abspath instead of SubPaths
def metadata_drop_applied_index(sub_paths: SubPaths) -> None:
    try:
        with open(sub_paths.metadata_abspath, "br") as f:
            metadata_lines = config_parse2(split_with_ts_bytes(f.read()))
    except FileNotFoundError:
        metadata_lines = empty_config_lines()

    metadata_lines = config_drop_key2(metadata_lines, b"subtree", b"appliedIndex")
    metadata_lines = config_drop_section_if_empty(metadata_lines, b"subtree")

    metadata_config = config_unparse2(metadata_lines)
    with open(sub_paths.metadata_abspath, "bw") as f:
        f.write(metadata_config)


def is_cwd_toplevel_directory(super_paths: SuperPaths) -> bool:
    return super_paths.super_to_cwd_relpath == b""


# TODO add "-z" option to be safe againts any chars in the path
# TODO add escpaing for "evil" chars in non "-z" output
# TODO add not about plumbing command
def cmd_list(args, parser) -> int:
    data = find_superproject()
    checked_data = check_superproject_data(data)
    superx = check_and_get_superproject_from_checked_data(checked_data)
    ensure_superproject_is_configured(superx)
    super_paths = gen_super_paths(superx.path)

    config = read_config(super_paths.config_abspath)

    for path in config.subprojects:
        # TODO Maybe avoid the decoded and encode dance
        print("%s" % (path.decode("utf8"),))

    return 0


def checks_for_cmds_with_single_subproject(enforce_cwd_is_subproject=True) -> tuple[Superproject, SuperPaths, SubPaths]:
    data = find_superproject()
    checked_data = check_superproject_data(data)
    superx = check_and_get_superproject_from_checked_data(checked_data)
    ensure_superproject_is_configured(superx)
    ensure_superproject_is_git(superx)

    # Check whether the current cwd is inside a subproject
    super_paths = gen_super_paths(superx.path)
    config = read_config(super_paths.config_abspath)

    # NOTE: This function can be used to select the subproject based on cwd!
    # TODO Refactor!
    super_to_sub_relpath = is_inside_subproject_and_return_path(config, super_paths)
    if super_to_sub_relpath is None:
        # TODO decided whether a wrong work directory is a invalid argument or a runtime error!
        raise AppException(ErrorCode.INVALID_ARGUMENT, "Current work directory must be inside a subproject!")

    if enforce_cwd_is_subproject:
        # NOTE: There is a nicer way to get get this information.
        # is_inside_subproject_and_return_path() already knows whether cwd is
        # at the subproject or not!
        if len(super_to_sub_relpath) == len(super_paths.super_to_cwd_relpath):
            assert super_to_sub_relpath == super_paths.super_to_cwd_relpath
            pass  # It's the same directory
        else:
            assert len(super_to_sub_relpath) < len(super_paths.super_to_cwd_relpath)
            assert super_paths.super_to_cwd_relpath.startswith(super_to_sub_relpath)
            #  l = len(super_to_sub_relpath)
            #  p = super_paths.super_to_cwd_relpath
            #  assert p[l] == ord("/")
            #  sub_to_cwd_relpath = p[l + 1:]
            #  # NOTE: above code is just for later refactoring!

            raise AppException(ErrorCode.INVALID_ARGUMENT,
                               "Current work directory must be the toplevel directory of the subproject for now!")

    sub_paths = gen_sub_paths_from_relpath(super_paths, super_to_sub_relpath)

    return superx, super_paths, sub_paths


# NOTE: Must be executed in the subprojects work tree
# TODO look at quilt. Mabye "apply" is the wrong term. But it would match "git apply"
# TODO Support applying multiple patches at once. Git also supports this.
def cmd_apply(args, parser):
    if args.path is None:
        raise AppException(ErrorCode.INVALID_ARGUMENT, "Must give a path to a patch file")

    if not os.path.isfile(args.path):
        raise AppException(ErrorCode.INVALID_ARGUMENT, "Path '%s' must point to a file!" % (args.path,))

    superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()
    metadata = read_metadata(sub_paths.metadata_abspath)
    subtree_dim = read_subtree_dim(metadata)
    patches_dim = read_patches_dim(sub_paths, metadata)
    ensure_dims_are_consistent(subtree_dim, patches_dim)

    if subtree_dim.applied_index is not None:
        # TODO Maybe check for linting error when default value is used!
        # TODO add message how to resolve it
        raise AppException(ErrorCode.INVALID_ARGUMENT, "Cannot apply new patch. Not all tracked patches are applied!")

    patch_filename = os.path.basename(args.path.encode("utf8"))

    if patch_filename in patches_dim.patches:
        raise AppException(ErrorCode.INVALID_ARGUMENT,
                           "The filename '%s' must be unique. There is already a patch with the same name!" %
                           (patch_filename.decode("utf8"),))

    # TODO Add DDx that patch file names must be in order for now!
    # TODO make DD: wether to keep name/number of patch or to rename/renumber it

    # TODO ugly code to check that the new patch file is sorted latest
    patches_new_sorted = sorted(patches_dim.patches + [patch_filename])
    if patches_new_sorted[-1] != patch_filename:
        # TODO add more info out to resolve the issue!
        raise AppException(ErrorCode.INVALID_ARGUMENT,
                           "The patch filenames must be in order. The new patch filename '%s' does not sort latest!" %
                           (patch_filename.decode("utf8"),))

    # Test whether the patch applies to the working tree
    # TODO refactor direct git call to to superproject helper!
    git_apply_args = ["git", "apply", "--allow-empty", "--index",
                      "--directory=%s" % (sub_paths.super_to_sub_relpath.decode("utf8"),), args.path]
    p = Popen(git_apply_args + ["--check"], stderr=DEVNULL)
    p.communicate()
    if p.returncode != 0:
        if p.returncode == 1:
            # TODO print infos how to test yourself and how to fix
            raise AppException(ErrorCode.INVALID_ARGUMENT,
                               "The patch '%s' does not apply to the working tree." % (patch_filename.decode("utf8"),))
        else:
            raise Exception("git failure")

    p = Popen(git_apply_args)
    p.communicate()
    if p.returncode != 0:
        # TODO add a nicer error message
        raise Exception("git failure")

    # TODO write this code nicer!
    if not os.path.exists(sub_paths.patches_abspath):
        os.makedirs(sub_paths.patches_abspath)

    shutil.copy(args.path.encode("utf8"), sub_paths.patches_abspath)
    super_to_patch_relpath = join(sub_paths.super_to_sub_relpath, b"patches", patch_filename)

    # TODO Thing about releative paths for SuperHelper
    with chdir(super_paths.super_abspath):
        superx.helper.add([super_to_patch_relpath])

    # For now cmd_apply only works when all tracked patches are applied. So the
    # code here does not need to update the 'appliedIndex' in the metadata.
    # Before "cmd_apply" all tracked patches are applied and after "cmd_apply"
    # all tracked patches are applied. The only differences is that there is
    # one additional patch now.

    if not args.quiet:
        # TODO The output convetion is wrong here. It should be relative and
        # the path to the subproject is not relative to the cwd here!
        print("Applied patch '%s' successfully!" % (args.path,))
        superx.helper.print_instructions_to_commit_and_inspect()

    return 0


def cmd_sync(args, parser):
    superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()
    metadata = read_metadata(sub_paths.metadata_abspath)
    subtree_dim = read_subtree_dim(metadata)
    patches_dim = read_patches_dim(sub_paths, metadata)
    ensure_dims_are_consistent(subtree_dim, patches_dim)

    if len(patches_dim.patches) == 0:
        raise AppException(ErrorCode.INVALID_ARGUMENT, "There is no current patch.")
    else:
        if subtree_dim.applied_index is None:
            # Ok case! There is at least one tracked patch and all patches are
            # applied! So there is a current patch!
            applied_index = len(patches_dim.patches) - 1
        elif subtree_dim.applied_index == -1:
            # TODO this is an invalid state or argument
            # TODO add explanation how to fix it!
            raise AppException(ErrorCode.INVALID_ARGUMENT, "There is no current patch.")
        else:
            applied_index = subtree_dim.applied_index

    # index checked by ensure_dims_are_consistent()
    patch_filename = patches_dim.patches[applied_index]
    patch_abspath = join(sub_paths.patches_abspath, patch_filename)
    patch_tmp_abspath = patch_abspath + b".tmp"

    # HACK for now nore
    # NOTE: we only want to have the diff of the subtree, not the "patches" dir and the ".subproject" file
    with chdir(super_paths.super_abspath):
        subtree_diff = superx.helper.get_diff_for_subtree(sub_paths.super_to_sub_relpath)
        subtree_stat = superx.helper.get_diff_for_subtree(sub_paths.super_to_sub_relpath, stat=True)

    # TODO cleanup tmpfile on exception
    # TODO move this to a patch file library
    with open(patch_abspath, "br") as f_old, open(patch_tmp_abspath, "bw") as f_new:
        before_diff = True
        after_diff = False
        for line in f_old:
            if before_diff:
                if line == b"---\n":
                    f_new.write(line)
                    # Write out the new diff
                    before_diff = False
                    f_new.write(subtree_stat)
                    f_new.write(b"\n")
                    f_new.write(subtree_diff)
                else:
                    # Write out the line as is
                    f_new.write(line)
            else:
                if not after_diff:
                    # Not yet after the original diff
                    if line == b"-- \n":
                        after_diff = True
                        # Write this line out
                        f_new.write(line)
                    else:
                        # drop this line, because it's the old diff
                        pass
                else:
                    # After the original diff, write out the original banner
                    f_new.write(line)

    os.rename(patch_tmp_abspath, patch_abspath)

    with chdir(super_paths.super_abspath):
        # TODO use relative paths. It feels nicer.
        superx.helper.add([patch_abspath])

    if not args.quiet:
        print("Syncing patch '%s' from stagging area." % (patch_filename.decode("utf8"),))
        # TODO make printout with superx.helper
        # NOTE This print out now clobbers a lot of the output of very command.
        # At some point the user knows it and this is just visual clutter.
        # Maybe have a config option to suppress it?
        # superx.helper.print_instructions_to_commit_and_inspect()

    return 0


# TODO Parts of this function must be moved to super.py
def do_patch_applys(superx: Superproject, super_paths: SuperPaths, sub_paths: SubPaths,
                    patches_dim: PatchesDim, from_applied_index: int, to_applied_index: int, quiet: bool) -> None:
    assert to_applied_index < len(patches_dim.patches)
    assert from_applied_index < len(patches_dim.patches)
    assert from_applied_index != to_applied_index
    assert from_applied_index >= -1
    assert to_applied_index >= -1

    args = ["git", "apply", "--allow-empty", "--index",
            "--directory=%s" % (sub_paths.super_to_sub_relpath.decode("utf8"),)]

    # index checked by ensure_dims_are_consistent()
    if from_applied_index > to_applied_index:
        # Popping patches
        indexes = range(from_applied_index, to_applied_index, - 1)
        reverse = True
    else:
        # Pushing patches
        indexes = range(from_applied_index + 1, to_applied_index + 1)
        reverse = False

    if reverse:
        args.append("--reverse")

    for i in indexes:
        patch_filename = patches_dim.patches[i]
        patch_abspath = join(sub_paths.patches_abspath, patch_filename)
        # TODO avoid abspath dance in the future. Code should be rel-path safe
        args.append(patch_abspath)

    # TODO check whether patchs applys fully before applying
    p = Popen(args)
    p.communicate()
    if p.returncode != 0:
        # TODO explain how to recover!
        raise Exception("git failure")

    if to_applied_index == len(patches_dim.patches) - 1:
        # Now all patches are applied. Drop the information from the metadata.
        # The default value is that all (tracked) patches are applied!
        metadata_drop_applied_index(sub_paths)
    else:
        metadata_set_applied_index(sub_paths, to_applied_index)

    with chdir(super_paths.super_abspath):
        # TODO here is not relative path used for git. This seems also to work!
        superx.helper.add([sub_paths.metadata_abspath])


def cmd_pop(args, parser):
    superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()
    metadata = read_metadata(sub_paths.metadata_abspath)
    subtree_dim = read_subtree_dim(metadata)
    patches_dim = read_patches_dim(sub_paths, metadata)
    ensure_dims_are_consistent(subtree_dim, patches_dim)

    # TODO same code in cmd_push. Maybe combine!
    if subtree_dim.applied_index is None:
        applied_index = len(patches_dim.patches) - 1
    else:
        applied_index = subtree_dim.applied_index

    if args.all:
        # NOTE: If there are no patches, "-a" exists successfully!
        if len(patches_dim.patches) == 0:
            print("The subproject does not track at least one patch. Nothing to pop!")
            return 0
        else:
            if applied_index == -1:
                print("No patches are applied. Nothing to pop!")
                return 0

        do_patch_applys(superx, super_paths, sub_paths, patches_dim, applied_index, -1, args.quiet)

        if not args.quiet:
            count_of_patches = applied_index + 1
            print("Poped %d patches successfully!" % (count_of_patches,))
    else:
        if len(patches_dim.patches) == 0:
            raise AppException(ErrorCode.INVALID_ARGUMENT, "The subproject does not track at least one patch. Nothing to pop!")
        else:
            if applied_index == -1:
                raise AppException(ErrorCode.INVALID_ARGUMENT, "No patches are applied. Nothing to pop!")

        do_patch_applys(superx, super_paths, sub_paths, patches_dim, applied_index, applied_index - 1, args.quiet)

        if not args.quiet:
            patch_filename = patches_dim.patches[applied_index]
            print("Poped patch '%s' successfully!" % (patch_filename.decode("utf8"),))

    if not args.quiet:
        superx.helper.print_instructions_to_commit_and_inspect()

    return 0


def cmd_push(args, parser):
    superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()
    metadata = read_metadata(sub_paths.metadata_abspath)
    subtree_dim = read_subtree_dim(metadata)
    patches_dim = read_patches_dim(sub_paths, metadata)
    ensure_dims_are_consistent(subtree_dim, patches_dim)

    if subtree_dim.applied_index is None:
        applied_index = len(patches_dim.patches) - 1
    else:
        applied_index = subtree_dim.applied_index

    if args.all:
        if len(patches_dim.patches) == 0:
            # TODO should this be printed to stderr?
            print("The subproject does not track at least one patch. Nothing to push!")
            return 0
        else:
            if applied_index == len(patches_dim.patches) - 1:
                print("All patches are applied. Nothing to push!")
                return 0

        do_patch_applys(superx, super_paths, sub_paths, patches_dim, applied_index, len(patches_dim.patches) - 1, args.quiet)
        if not args.quiet:
            count_of_patches = len(patches_dim.patches) - applied_index - 1
            print("Pushed %d patches successfully!" % (count_of_patches,))
    else:
        if len(patches_dim.patches) == 0:
            raise AppException(ErrorCode.INVALID_ARGUMENT, "The subproject does not track at least one patch. Nothing to push!")
        else:
            if subtree_dim.applied_index == len(patches_dim.patches) - 1:
                raise AppException(ErrorCode.INVALID_ARGUMENT, "All patches are applied. Nothing to push!")

        do_patch_applys(superx, super_paths, sub_paths, patches_dim, applied_index, applied_index + 1, args.quiet)

        if not args.quiet:
            patch_filename = patches_dim.patches[applied_index]
            print("Pushed patch '%s' successfully!" % (patch_filename.decode("utf8"),))

    if not args.quiet:
        superx.helper.print_instructions_to_commit_and_inspect()

    return 0


def do_init(super_paths: SuperPaths, sub_paths: SubPaths, superx: Superproject) -> None:
    # TODO check path argument
    # - Should not point outside the superproject
    # - should not point inside a existing subproject.

    if sub_paths.super_to_sub_relpath == b"":
        raise AppException(ErrorCode.INVALID_ARGUMENT,
                           "Subproject path is empty. Cannot create subproject at toplevel directory for now!")

    if os.path.exists(sub_paths.cwd_to_sub_relpath):
        # There is already a directory
        # TODO add message how to solve the problem
        # TODO just a empty dir should be ok!
        raise AppException(ErrorCode.INVALID_ARGUMENT,
                           "Directory '%s' alreay exists. Cannot add subproject!" % (sub_paths.cwd_to_sub_relpath.decode("utf8"),))

    if os.path.exists(sub_paths.metadata_abspath):
        # There is already a subproject at this place
        # TODO write this check better
        # TODO also check git index if there is a file
        # TODO explain what can be done: Either remove the dir or use another name!
        # TODO fix decode utf8. Should the the system default encoding!
        # TODO add tests for this!
        # TODO Add ErrorCode for invalid state of superproject.
        raise AppException(ErrorCode.INVALID_ARGUMENT,
                           "File '%s' alreay exists. Cannot add subproject!" % (sub_paths.metadata_abspath.decode("utf8"),))

    os.makedirs(sub_paths.cwd_to_sub_relpath)
    with open(join(sub_paths.cwd_to_sub_relpath, b".subproject"), "bw"):
        pass

    with chdir(super_paths.super_abspath):
        superx.helper.add([sub_paths.metadata_abspath])

    config_add_subproject(super_paths.config_abspath, sub_paths.super_to_sub_relpath)
    with chdir(super_paths.super_abspath):
        superx.helper.add([b".subpatch"])


def cmd_init(args, parser) -> int:
    data = find_superproject()
    checked_data = check_superproject_data(data)
    superx = check_and_get_superproject_from_checked_data(checked_data)
    ensure_superproject_is_configured(superx)
    # TODO for the simple command init, we maybe can relax this required even now!
    ensure_superproject_is_git(superx)
    super_paths = gen_super_paths(superx.path)

    # TODO ensure that paths are normalized!
    cwd_to_sub_relpath = args.path.rstrip("/").encode("utf8")
    sub_paths = gen_sub_paths_from_cwd_and_relpath(super_paths, cwd_to_sub_relpath)

    do_init(super_paths, sub_paths, superx)

    if not args.quiet:
        print("Subproject '%s' initialized." % (cwd_to_sub_relpath.decode("utf8"),))
        superx.helper.print_instructions_to_commit_and_inspect()

    return 0


def cmd_patches_list(args, parser):
    superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()

    metadata = read_metadata(sub_paths.metadata_abspath)
    patches_dim = read_patches_dim(sub_paths, metadata)

    for patch in patches_dim.patches:
        # TODO fix encoding
        # TODO should the output the path to the patch file or just the name of the patch file?
        # TODO should skipped/non-skipped state be shown here?
        # NOTE: the applied or not applied state cannot be shown, because the
        # information is in the subtree dimension
        print(patch.decode("utf8"))

    return 0


def cmd_subtree_checksum(args, parser):
    if sum(1 for x in [args.write, args.check, args.calc, args.get] if x) != 1:
        raise AppException(ErrorCode.INVALID_ARGUMENT, "You must exactly use one of --get, --calc, --write or --check!")

    superx, super_paths, sub_paths = checks_for_cmds_with_single_subproject()

    if args.calc:
        checksum = superx.helper.get_sha1_for_subtree(sub_paths.super_to_sub_relpath)
        print(checksum.decode("ascii"))
        return 0
    elif args.get:
        metadata = read_metadata(sub_paths.metadata_abspath)

        if metadata.subtree_checksum is None:
            # TODO This is not a INVALID_ARGUMENT, it's a state error
            # It's an ok state, because the subtree can be unpopluated
            raise AppException(ErrorCode.INVALID_ARGUMENT, "Subtree is unpopulated. So there is no checksum!")

        print(metadata.subtree_checksum.decode("ascii"))
        return 0
    elif args.check:
        checksum = superx.helper.get_sha1_for_subtree(sub_paths.super_to_sub_relpath)
        metadata = read_metadata(sub_paths.metadata_abspath)

        if metadata.subtree_checksum is None:
            # TODO is this a runtime error or an invalid argument?
            raise AppException(ErrorCode.INVALID_ARGUMENT, "No checksum in metadata found!")

        # TODO document exit codes
        # TODO maybe use abbrev versions of the checksum as git does!
        if checksum == metadata.subtree_checksum:
            if not args.quiet:
                checksum_str = checksum.decode("ascii")
                print(f"Subtree's checksum {checksum_str} matches the metdata!")
            return 0
        else:
            if not args.quiet:
                checksum_str = checksum.decode("ascii")
                metadata_checksum_str = metadata.subtree_checksum.decode("ascii")
                print(f"Subtree's checksum {checksum_str} does not match checksum {metadata_checksum_str} in the metadata.")
            return 1
    elif args.write:
        checksum = superx.helper.get_sha1_for_subtree(sub_paths.super_to_sub_relpath)

        # TODO mabye this should also have an output to stdout?
        metadata_set_subtree_checksum(sub_paths, checksum)

        return 0
    else:
        assert False


def do_status_subproject(super_paths: SuperPaths, subproject: bytes, changes) -> None:
    # TODO Idea: make it valid markdown output
    # TODO Idea: For every cvs superproject (superhelper) make the output
    # like the cvs styled of console output. Subpach should look like git
    # for git superprojects. And look like svn for svn superprojects.
    # NOTE: these two ideas are conflicting!

    # TODO use the term "dimensions" also in the output to make the
    # dimension for understandable for the user.

    sub_paths = gen_sub_paths_from_relpath(super_paths, subproject)
    metadata = read_metadata(sub_paths.metadata_abspath)

    # TODO again some bytes to string decoding. Annoying!
    subproject_str = subproject.decode("utf8")

    # TODO Think about other cvs systems
    print("# subproject at '%s'" % (subproject_str,))
    print("")

    # TODO add upstream dimensions
    if metadata.url is not None:
        print("* was integrated from URL: %s" % (metadata.url.decode("utf8"),))
    if metadata.revision is not None:
        print("* has integrated revision: %s" % (metadata.revision.decode("utf8"),))
        # TODO Maybe included whether it "tracks a branch" or it was a git tag
    if metadata.object_id is not None:
        print("* has integrated object id: %s" % (metadata.object_id.decode("utf8"),))

    # Get count of patches for subproject and other information
    patches_dim = read_patches_dim(sub_paths, metadata)
    subtree_dim = read_subtree_dim(metadata)
    ensure_dims_are_consistent(subtree_dim, patches_dim)

    p = subproject_str

    # NOTE Listing the modified files seems to much like "git status".
    # There is already "git status". The output just referneces the git
    # commands To inspect the changes.

    if subtree_dim.checksum == b"":
        print("""\
* Subtree is unpopulated""")

    if changes.untracked > 0:
        print("""\
* There are n=%d untracked files and/or directories:
    - To see them execute:
        `git status %s`
        `git ls-files --exclude-standard -o %s`
    - Use `git add %s` to add all of them
    - Use `git add %s/<filename>` to just add some of them
    - Use `rm <filename>` to remove them"""
              % (changes.untracked, p, p, p, p))

    if changes.unstaged > 0:
        print("""\
* There are n=%d modified files not staged for commit:
    - To see them execute:
        `git status %s` or
        `git diff %s`
    - Use `git add %s` to update what will be committed
    - Use `git restore %s` to discard changes in working directory"""
              % (changes.unstaged, p, p, p, p))

    if changes.uncommitted > 0:
        # TODO check git restore
        print("""\
* There are n=%d modified files that are staged, but not committed:
    - To see them execute:
        `git status %s` or
        `git diff --staged %s`
    - Use `git commit %s` to commit the changes
    - Use `git restore --staged %s` to unstage"""
              % (changes.uncommitted, p, p, p, p))
        # TODO check restore staged
        # TODO add command "git restore --staged --worktree -- xxxpath/"
        # to remove changes staged in the index from the index and the
        # working tree But leave changes in the working tree/unstaged
        # untouched This helps because it does ot leave new files in the
        # working tree as "git restore --staged" will done.

    patches_count = len(patches_dim.patches)
    if patches_count != 0:
        print("* There are n=%d patches." % (patches_count,))
        # TODO Maybe call this a "rebase" operation if not all patches are applied.
        if subtree_dim.applied_index is None:
            pass
        else:
            if subtree_dim.applied_index + 1 != patches_count:
                pass  # TODO May make this a linting error, because default value is used!
            print("* There are only n=%d patches applied." % (subtree_dim.applied_index + 1,))
            print("    - Use `subpatch push` to apply the next tracked patch to the subtree")

        # TODO implement subpatch patch list
        # print("    - Use `subpatch patches list` to list them")


# TODO add note that the output of "status" is not an API/plumbing. Should not be used in scripts
def cmd_status(args, parser):
    # TODO allow the cwd to select the subproject
    # TODO add plumbing commands for scripts!
    # TODO add colorscheme for output, e.g. like git status does
    # TODO handle stdout fd is pipe/file and not tty.

    data = find_superproject()
    checked_data = check_superproject_data(data)
    superx = check_and_get_superproject_from_checked_data(checked_data)
    ensure_superproject_is_configured(superx)
    ensure_superproject_is_git(superx)

    super_paths = gen_super_paths(superx.path)

    if not is_cwd_toplevel_directory(super_paths):
        print_warning = True
    else:
        print_warning = False

    config = read_config(super_paths.config_abspath)

    if args.path is not None:
        # TODO use sys default/argument encoding
        path_bytes = args.path.encode("utf8")
        path_relpath = os.path.relpath(path_bytes)
        super_to_sub_relpath = join(super_paths.super_to_cwd_relpath, path_relpath)

        # Normalize path. e.g. remove "." or ".." from the path!
        # TODO make this a common function and test it. Also the function
        # is_inside_subproject_and_return_path() does something similar!
        # TODO maybe add a plumbing command for that to expose to scripting!
        super_to_sub_relpath = os.path.normpath(super_to_sub_relpath)

        if super_to_sub_relpath not in config.subprojects:
            raise AppException(ErrorCode.INVALID_ARGUMENT,
                               "Argument '%s' does not point to a subproject!" % (args.path,))
        subprojects = [super_to_sub_relpath]
    else:
        # These are relative paths: super_to_sub_relpath
        subprojects = config.subprojects

    if len(subprojects) == 0:
        # Early return. Nothing to print!
        return 0

    # TODO does the concept of staged and unstaged files als exists in other
    # cvs systems
    with chdir(super_paths.super_abspath):
        # TODO make a test and use a real fix. For now just chdir to the
        # toplevel repo, but `git diff` is affected by the diff.relative option
        # that the user may have active or not.
        diff_files_not_staged = git_diff_name_only()
        diff_files_staged = git_diff_name_only(staged=True)

    # NOTE git_ls_files_untracked() depends on the cwd for now! Cwd must be the
    # root of the directory for now.
    with chdir(super_paths.super_abspath):
        ls_files_untrack = git_ls_files_untracked()

    # TODO refactor this struct and the following code to a function! And make
    # to interface for other cvs
    @dataclass
    class Changes:
        untracked: int = 0
        unstaged: int = 0
        uncommitted: int = 0

    subproject_changes = {}
    for path in subprojects:
        subproject_changes[path] = Changes()

    for subproject in subprojects:
        # TODO str vs bytes mismatch
        changes = subproject_changes[subproject]

        for path in ls_files_untrack:
            if path.startswith(subproject):
                changes.untracked += 1

        for path in diff_files_staged:
            if path.startswith(subproject):
                changes.uncommitted += 1

        for path in diff_files_not_staged:
            if path.startswith(subproject):
                changes.unstaged += 1

    print("NOTE: The format of the output is human-readable and unstable. Do not use in scripts!")
    print("NOTE: The format is markdown currently. Will mostly change in the future.")
    if print_warning:
        print("WARNING: The current working directory is not the toplevel directory of the superproject.")
        print("WARNING: The paths in this console output are wrong (for now)!")
    print("")

    for i, subproject in enumerate(subprojects):
        changes = subproject_changes[subproject]

        do_status_subproject(super_paths, subproject, changes)

        if i + 1 < len(subprojects):
            # Add a empty line between the subprojects
            print("")

    return 0


def main_wrapped() -> int:
    # TODO maybe add 'epilog' again
    parser = argparse.ArgumentParser(description='Adding subprojects into a git repo, the superproject.')
    parser.add_argument("--version", "-v", dest="version",
                        action="store_true", default=False,
                        help="Show version of program")
    parser.add_argument("--info", dest="info",
                        action="store_true", default=False,
                        help="Show more information, like homepage, repo and license")

    subparsers = parser.add_subparsers()

    parser_configure = subparsers.add_parser("configure",
                                             help="Configure the superproject to use subpatch")
    parser_configure.set_defaults(func=cmd_configure)
    parser_configure.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                                  help="Suppress output to stdout")

    parser_init = subparsers.add_parser("init",
                                        help="Init a subproject inside the superproject. Normaly done by subpatch add automatically.")
    parser_init.set_defaults(func=cmd_init)
    parser_init.add_argument(dest="path", type=str,
                             help="Path to new subproject")
    parser_init.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                             help="Suppress output to stdout")

    # TODO add argument to track a patch, but do not push/apply it.
    # -> would be the a command like "subpatch patch add <filename>", since it
    #    only uses the patch dimension.
    # The comamnd "subpatch apply" is a combination of
    #    "subpatch patch add <filename>" and
    #    "git apply <filename> == subpatch subtree apply <filename>"
    # TODO maybe the term apply is wrong here ... no it's not. git also uses apply!
    parser_apply = subparsers.add_parser("apply",
                                         help="Apply a patch to the subtree and add to patch list")
    parser_apply.set_defaults(func=cmd_apply)
    parser_apply.add_argument(dest="path", type=str,
                              help="Path to patch file")
    parser_apply.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                              help="Suppress output to stdout")

    # TODO think about exit code!
    parser_pop = subparsers.add_parser("pop",
                                       help="Remove current patch from the subtree")
    parser_pop.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                            help="Suppress output to stdout")
    parser_pop.add_argument("-a", "--all", action=argparse.BooleanOptionalAction,
                            help="Remove all patches")
    parser_pop.set_defaults(func=cmd_pop)

    parser_push = subparsers.add_parser("push",
                                        help="Apply the next patch to the subtree")
    parser_push.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                             help="Suppress output to stdout")
    parser_push.add_argument("-a", "--all", action=argparse.BooleanOptionalAction,
                             help="Apply all patches")
    parser_push.set_defaults(func=cmd_push)

    parser_add = subparsers.add_parser("add",
                                       help="Fetch and add a subproject")
    parser_add.set_defaults(func=cmd_add)
    parser_add.add_argument(dest="url", type=str,
                            help="URL or path to git repo")
    parser_add.add_argument(dest="path", type=str, default=None, nargs='?',
                            help="Add subproject a path (not use the repo name)")
    parser_add.add_argument("-r", "--revision", dest="revision", type=str,
                            help="Specify the revision to integrate. Can be a branch name, tag name or commit id.")
    parser_add.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                            help="Suppress output to stdout")

    # TODO maybe find better name than "sync"
    parser_sync = subparsers.add_parser("sync",
                                        help="Update diff of the current patch from the staging area")
    parser_sync.set_defaults(func=cmd_sync)
    parser_sync.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                             help="Suppress output to stdout")

    parser_update = subparsers.add_parser("update",
                                          help="Fetch and update a subproject")
    parser_update.set_defaults(func=cmd_update)
    parser_update.add_argument(dest="path", type=str, default=None, nargs='?',
                               help="path to subproject")
    parser_update.add_argument("--url", dest="url", type=str,
                               help="URL or path to the remote git repo")
    parser_update.add_argument("-r", "--revision", dest="revision", type=str,
                               help="Specify the revision to integrate. Can be a branch name, tag name or commit id.")
    parser_update.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                               help="Suppress output to stdout")

    parser_status = subparsers.add_parser("status",
                                          help="Prints a summary of all or one subprojects")
    parser_status.set_defaults(func=cmd_status)
    parser_status.add_argument(dest="path", type=str, default=None, nargs='?',
                               help="path to a subproject")

    parser_list = subparsers.add_parser("list",
                                        help="List all subprojects")
    parser_list.set_defaults(func=cmd_list)

    parser_patches = subparsers.add_parser("patches",
                                           help="Commands to modify/query the subprojects patches")
    subparsers_patches = parser_patches.add_subparsers()
    parser_patches_list = subparsers_patches.add_parser("list",
                                                        help="List tracked patches in the subproject")
    parser_patches_list.set_defaults(func=cmd_patches_list)

    parser_subtree = subparsers.add_parser("subtree",
                                           help="Commands to modify/query the subprojects subtree")
    subparsers_subtree = parser_subtree.add_subparsers()
    parser_subtree_checksum = subparsers_subtree.add_parser("checksum",
                                                            help="Commands to modify/query the checksum of the subtree")
    # TODO these options are actually commands. It's only allowed to give on option! refactor!
    parser_subtree_checksum.add_argument("--calc", dest="calc", action=argparse.BooleanOptionalAction,
                                         help="tbd")
    parser_subtree_checksum.add_argument("--check", dest="check", action=argparse.BooleanOptionalAction,
                                         help="tbd")
    parser_subtree_checksum.add_argument("--write", dest="write", action=argparse.BooleanOptionalAction,
                                         help="tbd")
    parser_subtree_checksum.add_argument("--get", dest="get", action=argparse.BooleanOptionalAction,
                                         help="tbd")
    parser_subtree_checksum.add_argument("-q", "--quiet", action=argparse.BooleanOptionalAction,
                                         help="Suppress output to stdout")
    parser_subtree_checksum.set_defaults(func=cmd_subtree_checksum)

    parser_help = subparsers.add_parser("help",
                                        help="Also shows the help message")
    parser_help.set_defaults(func=cmd_help)

    args = parser.parse_args()

    # Just for testing. A bit ugly to have this in the production code.
    signal_file_path = os.environ.get("HANG_FOR_TEST", "")
    if len(signal_file_path) > 0:
        with open(signal_file_path, "bw") as f:
            f.write(b"")
        time.sleep(100)

    if args.version:
        ret = show_version(args)
    elif args.info:
        ret = show_info(args)
    else:
        # Workaround for help
        if hasattr(args, "func"):
            ret = args.func(args, parser)
        else:
            ret = nocommand(args, parser)

    return ret


def main() -> int:
    try:
        ret = main_wrapped()

        # For some functions I have forgotten to add a return statement. Catch
        # this bug here!
        assert ret is not None

        return ret
    except AppException as e:
        # TODO allow to append a generic error message for all messages, not only for invalid argument.
        if e._code == ErrorCode.NOT_IMPLEMENTED_YET:
            # TODO the message should show the github issue url!
            print("Error: Feature not implemented yet: %s" % (e,), file=sys.stderr)
        elif e._code == ErrorCode.SUPERPROJECT_NOT_FOUND:
            # TODO add steps to resolve the issue. e.g. touching the file
            print("Error: No superproject found!", file=sys.stderr)
        elif e._code == ErrorCode.SUPERPROJECT_NOT_CONFIGURED:
            # TODO add steps to resolve the issue. e.g. touching the file
            # TODO rework error message, Word subpatch should not be included
            print("Error: subpatch not yet configured for superproject!", file=sys.stderr)
        elif e._code == ErrorCode.INVALID_ARGUMENT:
            # TODO change structure of errors. It contains two colons now.
            # Looks ugly.
            print("Error: Invalid argument: %s" % (e,), file=sys.stderr)
        elif e._code == ErrorCode.INVALID_STATE:
            # TODO change structure of errors. It contains two colons now.
            # Looks ugly.
            print("Error: Invalid state: %s" % (e,), file=sys.stderr)
        elif e._code == ErrorCode.CUSTOM:
            print("Error: %s" % (e,), file=sys.stderr)
        else:
            assert False
        return 4
    except KeyboardInterrupt:
        print("Interrupted!", file=sys.stderr)
        # TODO What is the correct/best error code?
        return 3


if __name__ == '__main__':
    sys.exit(main())
