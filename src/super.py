import os
import stat
from dataclasses import dataclass
from contextlib import chdir
from enum import Enum
from os.path import abspath, join

# ----8<----
from git import (git_add, git_diff_staged_shortstat, git_cat_file_pretty,
                 git_hash_object_tree)
# TODO decide wether also CacheHelper can use the AppException or should use a
# own exception
from util import AppException, ErrorCode
# ----8<----

# TODO For me it's not clear yet if this file should only contain the
# SuperHelper implementations or more super stuff! Decided it


class SCMType(Enum):
    GIT = b"git"


class SuperprojectType(Enum):
    PLAIN = b"plain"
    GIT = b"git"


# NOTE: In both cases it's the path to the toplevel directory!
@dataclass
class FindSuperprojectData:
    super_path: bytes | None = None
    scm_type: SCMType | None = None
    scm_path: bytes | None = None


# Based on the current work directory search for a ".subpatch" file and SCM
# system.
#
# TODO support svn, mercurial and others in the future
# TODO thinking about symlinks!
def find_superproject() -> FindSuperprojectData:
    abs_cwd = abspath(os.getcwdb())

    # TODO refactory this self-made and hacky approach of a directory walk
    # The first element is empty, because of the absolute path.  But using a
    # empty element in "join" does not work. It's the reverse operation!
    assert abs_cwd[0] == ord("/")
    abs_cwd_parts = os.path.normpath(abs_cwd).split(b"/")
    assert abs_cwd_parts[0] == b""
    abs_cwd_parts.pop(0)

    statinfo = os.stat(abs_cwd)
    assert stat.S_ISDIR(statinfo.st_mode)

    cwd_st_dev = statinfo.st_dev

    data = FindSuperprojectData()

    while True:
        abs_cur_path = join(b"/", *abs_cwd_parts)

        statinfo = os.stat(abs_cur_path)
        if statinfo.st_dev != cwd_st_dev:
            # The directory walk leaves the current filesystem. This is a stop
            # condition for now.
            # TODO Maybe implement 'GIT_DISCOVERY_ACROSS_FILESYSTEM'
            # See https://git-scm.com/docs/git.html#Documentation/git.txt-codeGITDISCOVERYACROSSFILESYSTEMcode
            break

        if data.super_path is None:
            if os.path.exists(join(abs_cur_path, b".subpatch")):
                # Configuration file found
                data.super_path = abs_cur_path

        if data.scm_type is None:
            # NOTE Simple implementation. Check whether there is a ".git"
            # folder next to it.
            # Does not work for git-worktrees! ... really? TODO check it!
            if os.path.exists(join(abs_cur_path, b".git")):
                data.scm_type = SCMType.GIT
                data.scm_path = abs_cur_path

        if data.super_path is not None and data.scm_type is not None:
            # If both is already found, stop the directory walk
            break

        if len(abs_cwd_parts) == 0:
            break

        abs_cwd_parts.pop()

    return data


# TODO There is still reduance in the structure!
@dataclass(frozen=True)
class CheckedSuperprojectData:
    super_path: bytes
    configured: bool
    scm_type: SCMType | None


# There can be four cases
#  - no ".subpatch" config and no SCM
#     -> function returns None
#  - ".subpatch" config and no SCM
#  - no ".subpach" config and SCM
#  - ".subpach" config and SCM
# For the last cases there are two sub-cases:
#  - super_path matches scm_path
#  - both paths do not match
def check_superproject_data(data: FindSuperprojectData) -> CheckedSuperprojectData | None:
    if data.scm_type is not None:
        # There is a SCM tool
        if data.super_path is None:
            # And there is no subpatch config file
            assert data.scm_path is not None
            return CheckedSuperprojectData(data.scm_path, False, data.scm_type)
        else:
            # And there is a subpatch config file!

            # Check if the paths match up:
            if data.super_path != data.scm_path:
                # TODO add text here!
                # TODO rename "root" to "toplevel" to be consistent.
                raise AppException(ErrorCode.NOT_IMPLEMENTED_YET, "subpatch config file is not at the root of the SCM repository!")

            return CheckedSuperprojectData(data.super_path, True, data.scm_type)
    else:
        # Current working directory is not in a SCM system
        if data.super_path is None:
            # And there is no subpatch config file
            return None
        else:
            # And there is a subpatch config file
            return CheckedSuperprojectData(data.super_path, True, data.scm_type)


# TODO clarify naming: path, filename, url
# TODO clairfy name for remote git name and path/url

class SuperHelperPlain:
    def add(self, paths: list[bytes]) -> None:
        # Nothing to do here. There is no SCM system. So the code can also not add
        # files to the SCM
        pass

    def print_instructions_to_commit_and_inspect(self) -> None:
        raise NotImplementedError("TODO think about this case!")

    def configure(self, scm_path: bytes) -> None:
        raise NotImplementedError("TODO think about this case!")

    def get_sha1_for_subtree(self, path: bytes) -> bytes:
        raise NotImplementedError("TODO think about this case!")


# TODO think about the data structure every super_helper method gets!
class SuperHelperGit:
    # Add the file in 'path' to the index
    # TODO not all version control systems have the notion of a index!
    def add(self, paths: list[bytes]) -> None:
        git_add(paths)

    def print_instructions_to_commit_and_inspect(self) -> None:
        shortstat = git_diff_staged_shortstat()
        if shortstat == b"":
            print("Note: There are no changes in the subproject. Nothing to commit!")
        else:
            print("The following changes are recorded in the git index:")
            print("%s" % (shortstat.decode("ascii"),))
            print("- To inspect the changes, use `git status` and `git diff --staged`.")
            print("- If you want to keep the changes, commit them with `git commit`.")
            print("- If you want to revert the changes, execute `git reset --merge`.")

    # TODO move this code to "main.py" it's generic for all SCMs
    def configure(self, scm_path: bytes) -> None:
        config_abspath = join(scm_path, b".subpatch")
        assert not os.path.exists(config_abspath)
        with open(config_abspath, "bw"):
            pass

        # TODO: Using cwd to the toplevel directory is just a hack because
        # the helper is cwd-aware.
        with chdir(scm_path):
            git_add([b".subpatch"])

    def print_configure_success(self) -> None:
        print("The file .subpatch was created in the toplevel directory.")
        print("Now use 'git commit' to finalized your change.")
        # TODO maybe use the same help text as "add" and "update".

    # Compute the checkums as a git sha1 for the subtree/worktree of the
    # subproject.
    # NOTE: This must take files in the index into account!
    def get_sha1_for_subtree(self, super_to_sub_relpath: bytes) -> bytes:
        # TODO this function is just a hacky first version. There at least path
        # escaping any mabye other problems!

        # TODO maybe use "ls-tree -z" instead of "HEAD:<path>" syntax. Escaping is easier!
        import subprocess
        p = subprocess.Popen([b"git", b"write-tree", b"--prefix=" + super_to_sub_relpath], stdout=subprocess.PIPE)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("here")

        sha1 = stdout.rstrip(b"\n")

        return self.strip_tree_object(sha1)

    # TODO refactor!!!!
    # TODO Move function to git.py. It's should not be part of the SuperHepler!
    def strip_tree_object(self, sha1: bytes) -> bytes:
        tree_data_pretty = git_cat_file_pretty(sha1)

        # The pretty format looks like
        #    100644 blob bf252b96c379a66383f5ac9b605b1633bd39362e\ta
        #    100644 blob bf252b96c379a66383f5ac9b605b1633bd39362e\tb

        tree_data_pretty_stripped = []
        for line in tree_data_pretty.split(b"\n"):
            if line == b"":
                continue
            if line.endswith(b"\tpatches") or line.endswith(b"\t.subproject"):
                pass
            else:
                tree_data_pretty_stripped.append(line)

        # TODO git git specifc stuff should be in the "git.py" file
        # The binary format looks like
        #    <mode in octal> <one space> <filename> <NULL byte> <SHA1 as bytes>

        # Convert from pretty into binary format
        new_tree_data = b""
        for line in tree_data_pretty_stripped:
            mode_type_sha1, path = line.split(b"\t", 1)
            mode, _, sha1 = mode_type_sha1.split(b" ")
            # Convert mode
            if mode == b"040000":
                mode = b"40000"
            new_tree_data += mode + b" " + path + b"\0" + bytearray.fromhex(sha1.decode("ascii"))

        return git_hash_object_tree(new_tree_data)

    # TODO argument 'stat' is kind of a hack for now!
    def get_diff_for_subtree(self, super_to_sub_relpath: bytes, stat: bool = False) -> bytes:
        # For the current staged files in the subtree, get a SHA1 sum of the
        # tree object, without the ".subproject" and "patches changes"
        subtree_staged_sha1 = self.get_sha1_for_subtree(super_to_sub_relpath)

        subtree_head_sha1 = self.strip_tree_object(b"HEAD:" + super_to_sub_relpath)

        import subprocess
        cmd = [b"git", b"diff", "--relative", subtree_head_sha1, subtree_staged_sha1]
        if stat:
            cmd.append("--stat")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, _ = p.communicate()
        if p.returncode != 0:
            raise Exception("here")

        return stdout


# TODO compare to CheckedSuperprojectData. It's very similiar, maybe refactor
@dataclass(frozen=True)
class Superproject:
    path: bytes
    helper: SuperHelperGit | SuperHelperPlain
    configured: bool
    typex: SuperprojectType   # TODO same information is in 'helper'. Refactor!


def check_and_get_superproject_from_checked_data(checked_data: CheckedSuperprojectData | None) -> Superproject:
    # TODO maybe move outside of this function
    if checked_data is None:
        # And there is no subpatch config file and no SCM
        raise AppException(ErrorCode.SUPERPROJECT_NOT_FOUND)

    if checked_data.scm_type is not None:
        # There is a SCM tool
        # And there is either a subpatch config file or not: See value of 'configured'
        if checked_data.scm_type == SCMType.GIT:
            super_type = SuperprojectType.GIT
            helper = SuperHelperGit()
        else:
            raise AppException(ErrorCode.NOT_IMPLEMENTED_YET, "SCM tool '%s' not implemented yet" % (checked_data.scm_type,))
    else:
        # Current working directory is not in a SCM system.  But there is a
        # config file. Ensured by the caller!
        assert checked_data.configured
        helper = SuperHelperPlain()
        super_type = SuperprojectType.PLAIN

    super_path = checked_data.super_path
    configured = checked_data.configured

    return Superproject(super_path, helper, configured, super_type)
