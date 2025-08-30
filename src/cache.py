import os
import shutil
from contextlib import chdir
from dataclasses import dataclass
from os.path import join
from typing import Any

# ----8<----
from git import (ObjectType, git_clone, git_get_object_type, git_get_sha1,
                 git_init_and_fetch, git_ls_remote_guess_ref, git_reset_hard,
                 git_verify, is_sha1)
# TODO decide wether also CacheHelper can use the AppException or should use a
# own exception
from util import AppException, ErrorCode, URLTypes, get_url_type

# ----8<----


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

    # Download remote repository, checkout the request revision, remove
    # repository metadata and leave the plan files in the dir 'cache_relpath'.
    # NOTE: return value is either a object_id of a tag or of a commit!
    def download(self, download_config: DownloadConfig, folder) -> bytes:
        # NOTE "git submodule init" creates a bare repository in ".git/modules"
        # TODO maybe also use that folder as a scrat pad.
        # TODO clone only a single branch and maybe use --depth 1
        #  - that is already partially implemented
        # TODO handle potential submodules in the subproject correctly

        url = download_config.url
        revision = download_config.revision  # Can be None

        clone_config = git_resolve_to_clone_config(url, revision)

        # TODO optimization. If it's a local git repo, use --reference to share
        # object store.

        # There are three cases:
        #   - full clone + with object id
        #   - full clone + without object id
        #   - fetch + with ref
        if clone_config.full_clone:
            git_clone(url, folder)
            if clone_config.object_id is not None:
                with chdir(folder):
                    if not git_verify(clone_config.object_id):
                        # TODO use context wrapper for cleanup!
                        shutil.rmtree(b"../" + folder)
                        raise AppException(ErrorCode.INVALID_ARGUMENT,
                                           "Object id '%s' does not point to a valid object!" % (clone_config.object_id,))

                    object_type = git_get_object_type(clone_config.object_id)
                    if object_type not in (ObjectType.COMMIT, ObjectType.TAG):
                        # TODO use context wrapper for cleanup!
                        shutil.rmtree(b"../" + folder)
                        raise AppException(ErrorCode.INVALID_ARGUMENT,
                                           "Object id '%s' does not point to a commit or tag object!" % (clone_config.object_id,))

                    git_reset_hard(clone_config.object_id)
                object_id = clone_config.object_id.encode("ascii")
            else:
                with chdir(folder):
                    object_id = git_get_sha1("HEAD")
        else:
            # TODO This is really ugly!
            assert not os.path.isabs(folder)
            assert b"//" not in folder  # sanitze path
            folder_count = folder.rstrip(b"/").count(b"/") + 1

            os.makedirs(folder)
            with chdir(folder):
                # TODO Not work with relative paths, because a subdir is used!
                if get_url_type(url) == URLTypes.LOCAL_RELATIVE:
                    # This is ugly!
                    # TODO fix str bs byte missmatch. encode should not be needed here!
                    url_tmp = b"../" * folder_count + url.encode("utf8")
                else:
                    url_tmp = url
                # TODO Rework DownloadConfig to avoid extra asser here
                assert clone_config.ref is not None
                object_id = git_init_and_fetch(url_tmp, clone_config.ref)
                git_reset_hard(object_id)

        # Remove ".git" folder in this repo
        # TODO this must be moved outside of the download function. It should
        # be persistent.
        local_repo_git_dir = join(folder, b".git")
        assert os.path.isdir(local_repo_git_dir)
        shutil.rmtree(local_repo_git_dir)

        return object_id
