import os
from contextlib import chdir
from dataclasses import dataclass
from typing import Any
from os.path import join
from subprocess import DEVNULL, Popen

# ----8<----
from libgit import (ObjectType, git_get_object_type, git_ls_remote_guess_ref,
                    git_verify, is_sha1, git_init_bare, git_fetch)
from util import AppException, ErrorCode, URLTypes, get_url_type

# ----8<----


# TODO Make this of type "bytes". It's currentl 'str'.
@dataclass(frozen=True)
class DownloadConfig:
    url: Any
    revision: Any | None = None


@dataclass(frozen=True)
class CloneConfig:
    full_clone: bool
    object_id: str | None = None
    ref: bytes | None = None


def git_resolve_to_clone_config(url: str, revision: str | None) -> CloneConfig:
    # Some heuristics to sort out branch, commit/tag id or tag
    if revision is not None:

        # TODO Clean type missmatch
        assert isinstance(revision, str)
        revision_bytes = revision.encode("utf8")

        if is_sha1(revision_bytes):
            # NOTE Commit ids are bad! You cannot download just a single
            # commit id. You can only clone everything and hope that the commit id
            # is in there!
            # TODO Handle tag ids special. They can be looked up by "git
            # ls-remote".
            return CloneConfig(full_clone=True, object_id=revision)
        else:
            # It looks like a ref to a branch or tag. Try to resolve it
            ref_resolved = git_ls_remote_guess_ref(url, revision)
            if ref_resolved is None:
                raise AppException(ErrorCode.INVALID_ARGUMENT,
                                   "The reference '%s' cannot be resolved to a branch or tag!" % (revision,))
            return CloneConfig(full_clone=False, ref=ref_resolved)
    else:
        # Use HEAD of remote repository
        # TODO optimize this by looking at the output of "git ls-remote".
        return CloneConfig(full_clone=True)


class CacheHelperGit:
    def get_revision_as_str(self, revision: str | None) -> str:
        # The revision is of type Optional<str>. It's either None or a str.
        # Convert to a printable string for stdout
        if revision is None:
            return "HEAD"
        return revision

    # TODO allow to use bare and non-bare git repositories
    # NOTE "git submodule init" creates a bare repository in ".git/modules"
    def create(self, cwd_to_cache_relpath: bytes) -> None:
        assert os.path.isdir(cwd_to_cache_relpath)
        with chdir(cwd_to_cache_relpath):
            git_init_bare()
        # TODO add are enfore that there is a cache-subpatch config file

    def isCreated(self, cwd_to_cache_relpath: bytes) -> bool:
        # Very simple check to test whether the cache directory contains a bare
        # git repository.
        # TODO also check for cache subpatch config file
        return os.path.isfile(join(cwd_to_cache_relpath, b"config"))

    # TODO return the object id here is maybe not correct, because it's not
    # agnostic to other cache types.
    # NOTE: return value is either a object_id of a tag or of a commit!
    def fetch(self, cwd_to_cache_relpath: bytes, download_config: DownloadConfig) -> bytes:
        # TODO clone only a single branch and maybe use --depth 1
        #  - that is already partially implemented
        url = download_config.url
        revision = download_config.revision  # Can be None

        clone_config = git_resolve_to_clone_config(url, revision)

        assert not os.path.isabs(cwd_to_cache_relpath)
        assert b"//" not in cwd_to_cache_relpath  # sanitze path
        folder_count = cwd_to_cache_relpath.rstrip(b"/").count(b"/") + 1

        # TODO Not work with relative paths, because a subdir is used!
        if get_url_type(url) == URLTypes.LOCAL_RELATIVE:
            # This is ugly!
            # TODO fix str bs byte missmatch. encode should not be needed here!
            url_tmp = b"../" * folder_count + url.encode("utf8")
        else:
            url_tmp = url

        with chdir(cwd_to_cache_relpath):
            # There are three cases:
            #   - full clone + with object id
            #   - full clone + without object id
            #   - fetch + with ref
            if clone_config.full_clone:
                # We have to fetch all remote refs (heads and tags), because we
                # don't know in which refs the commit/tag(=object id) exists.
                object_id = git_fetch(url_tmp, '*:*')

                if clone_config.object_id is not None:
                    if not git_verify(clone_config.object_id):
                        raise AppException(ErrorCode.INVALID_ARGUMENT,
                                           "Object id '%s' does not point to a valid object!" % (clone_config.object_id,))

                    object_type = git_get_object_type(clone_config.object_id)
                    if object_type not in (ObjectType.COMMIT, ObjectType.TAG):
                        raise AppException(ErrorCode.INVALID_ARGUMENT,
                                           "Object id '%s' does not point to a commit or tag object!" % (clone_config.object_id,))
                    # The requested object_id exists and is a tag or commit. We can use it!
                    object_id = clone_config.object_id.encode("ascii")
            else:
                # TODO Rework DownloadConfig to avoid extra asser here
                assert clone_config.ref is not None
                object_id = git_fetch(url_tmp, clone_config.ref)

        return object_id

    # Extracts all files into the folder "dest_relpath" inside the cache.
    def extract(self, cwd_to_cache_relpath: bytes, object_id: bytes, dest_relpath: bytes) -> bytes:
        # TODO clean this up! and add tests!
        # For now very ugly and just get it done
        with chdir(cwd_to_cache_relpath):
            p = Popen(["git", "worktree", "add", "-q", "--detach", dest_relpath, object_id], stdout=DEVNULL)
            p.communicate()
            if p.returncode != 0:
                raise Exception("error here")

            # Very ugly. Afterwards the repo is in a invalid state. The work
            # tree is broken! Only works because the cache is removed anyway
            # afterwards!
            with chdir(dest_relpath):
                # Remove the link to the git directory, to make the directory a clean checkout!
                assert os.path.isfile(".git")
                os.remove(".git")
