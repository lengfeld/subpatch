from enum import Enum
from typing import Dict, Optional
from subprocess import PIPE
# ----8<----
import os
from subprocess import Popen, DEVNULL
# ----8<----

# Git naming
#  - object: something in the object store that has a SHA1
#  - object type: type of the object. Can be blob, tree, commit or tag.
#  - object id: the hash of the object (taken from the git source code)
#  - ref: short for "reference", like branches and tags.
#         Everything in the 'refs' folder/namespace
#  - rev: short for "revision"
#     "A revision parameter <rev> typically, but not necessarily, names a
#     commit object." See 'man gitrevisions'
#     E.g. a <sha1>, "HEAD", "x..y" or "main:file"


def git_add(args):
    assert len(args) >= 1
    # NOTE: use "-f" here otherwise git honors ignored files and does not add
    # all files!
    p = Popen(["git", "add", "-f"] + args)
    p.communicate()
    if p.returncode != 0:
        raise Exception("git failure")


def git_diff_staged_shortstat():
    p = Popen(["git", "diff", "--staged", "--shortstat"], stdout=PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("git failure")

    stdout = stdout.rstrip(b"\n")
    assert isinstance(stdout, bytes)
    return stdout


# As of git v2.9.0 these are all valid git objects
OBJECT_TYPES = (b"blob", b"tree", b"commit", b"tag")


class ObjectType(Enum):
    BLOB = b"blob"
    TREE = b"tree"
    COMMIT = b"commit"
    TAG = b"tag"


# Returns the type of the git object
# TODO not used yet. Implement sanity check
# TODO naming 'rev' is incorrect. 'rev' is only for commit objects.
def git_get_object_type(rev: str) -> ObjectType:
    p = Popen(["git", "cat-file", "-t", rev], stdout=PIPE, stderr=DEVNULL)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        # TODO Create a generic git error exception
        raise Exception("failed here")

    stdout = stdout.rstrip(b"\n")
    assert stdout in OBJECT_TYPES
    if stdout == b"blob":
        return ObjectType.BLOB
    elif stdout == b"tree":
        return ObjectType.TREE
    elif stdout == b"commit":
        return ObjectType.COMMIT
    return ObjectType.TAG


# Convert URLs. Examples:
#     …bla/foo/.git/ -> "foo"
#     …bla/foo.git/  -> "foo"
#     …bla/foo       -> "foo"
def get_name_from_repository_url(url: str):
    if len(url) == 0:
        raise ValueError("The URL is empty!")
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    url = url.rstrip("/")
    url = url.split("/")[-1]
    return url


# Check whether the 'rev' can be resolved to a valid object in the repository
# NOTE:
# - If this command is not exectued in a git repo, it raises an exception.
def git_verify(rev: str) -> bool:
    p = Popen(["git", "rev-parse", "--quiet", "--verify", rev + "^{object}"],
              stdout=DEVNULL, stderr=DEVNULL)
    p.communicate()
    if p.returncode == 1:
        return False
    if p.returncode != 0:
        # Example stderr output:
        #   fatal: not a git repository (or any of the parent directories): .git
        # TODO replace with git specific exception
        raise Exception("todo")

    return True


def is_valid_revision(revision: str) -> bool:
    # TODO add more invalid and strange chars to this list
    # TODO eval svn, git, ... for allow characters. What about umlauts?
    strange_chars = ("\t", "\n", "\b")
    for char in strange_chars:
        if char in revision:
            return False
    return True


# TODO add example of input
# TODO add more tests, e.g. with syntax errors or duplicated refs.
def parse_sha1_names(lines: bytes, sep=b' ') -> Dict[bytes, bytes]:
    # remove the last new line character
    # Should only be one character
    lines = lines.rstrip(b'\n')

    # Ignore empty lines
    lines1 = [line.split(sep) for line in lines.split(b'\n') if len(line) != 0]

    for line in lines1:
        if len(line) != 2:
            raise Exception("Parsing error in line: sep = %s parts = %s" % (sep, line))
    lines2 = [(name, sha1) for sha1, name in lines1]

    # checks
    for _, sha1 in lines2:
        if not is_sha1(sha1):
            raise ValueError("String is not a SHA1 sum: %r" % (sha1,))

    return dict(lines2)


def git_get_sha1(rev):
    # NOTE: Special case for valid SHA1 sums. Even if the object for the
    # SHA1 does not exist in the repo, it's return as a valid SHA1 If the
    # rev is a too short SHA1, it's extend to a full SHA1 if a object with
    # the short SHA1 exists in the repo.
    p = Popen(["git", "rev-parse", "-q", "--verify", rev], stdout=PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("error here TODO")

    return stdout.rstrip(b"\n")


# git_ls_remote ::  string(url) -> dict<ref_name, sha1>
# Output contains branches, tags, tag-commitisch "^{}" and the HEAD.
def git_ls_remote(url: str) -> Dict[bytes, bytes]:
    # NOTE Subpress stderr output of 'ls-remote'. In case of a fetch failure
    # stuff is written to stderr.

    p = Popen(["git", "ls-remote", url], stdout=PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("git ls-remote failed")

    # Parse output
    # The output of ls-remote uses the tab character as the separator. The
    # show-ref command uses spaces.
    return parse_sha1_names(stdout, sep=b'\t')


# Query the remote git repo and try to resolve the 'ref'.
# E.g.
#  - "main" -> "refs/heads/main"
#  - "v1" -> "refs/tags/v1"
# Notes:
#  - function accepts ref as string, but returns a byte Object!
# Returns
#  - None if ref could not be resolved
# TODO also return the matched object
def git_ls_remote_guess_ref(url: str, ref_str: str) -> Optional[bytes]:
    # TODO "git ls-remote" also allows to query a single ref or a pattern of
    # refs!
    refs_sha1 = git_ls_remote(url)

    ref = ref_str.encode("utf8")

    if ref in refs_sha1:
        return ref  # Direct match

    ref_as_tag = b"refs/tags/" + ref
    if ref_as_tag in refs_sha1:
        return ref_as_tag

    ref_as_branch = b"refs/heads/" + ref
    if ref_as_branch in refs_sha1:
        return ref_as_branch

    return None


# Parse the "-z" output of git commands
# TODO rework as a generator
def parse_z(b: bytes) -> list[bytes]:
    if b == b"":
        # Special case. b"".split(b"\0") is [b""], but
        # we want a list without elements here.
        return []

    return b.rstrip(b"\0").split(b"\0")


def git_diff_in_dir(top_dir, subdir, staged=False):
    # TODO verify that top_dir is the toplevel dir in the repo
    # -> Refactor to git object or class that checks the top_dir
    # TODO check that subdir is a relative and a sane path!
    cmd = ["git", "diff", "--name-only", "-z"]
    if staged:
        cmd += ["--staged"]
    cmd += ["--", subdir]

    p = Popen(cmd, stdout=PIPE, cwd=top_dir)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("error here")

    return len(stdout) != 0


# NOTE: argument and output is not cwd aware. It's always relative to the
# toplevel of the git repository.
def git_ls_tree_in_dir(subdir):
    assert isinstance(subdir, bytes)

    if subdir == b"":
        subdir = b"."

    p = Popen(["git", "ls-tree", "--full-tree", "-r", "--name-only", "-z", "HEAD", subdir],
              stdout=PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("TODO error here")

    return parse_z(stdout)


def git_diff_name_only(staged=False):
    # NOTE: "git diff" does not depend on the cwd inside the repo
    cmd = ["git", "diff", "--name-only", "-z"]
    if staged:
        cmd += ["--staged"]

    p = Popen(cmd, stdout=PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        raise Exception("error here")

    return parse_z(stdout)


# NOTE: This depends on the cwd for now. git ls-files has no option to force
# listing files from the top level directory.
# TODO fix that
def git_ls_files_untracked():
    # TODO refactor common code
    # NOTE:
    # - Use "--full-name" to make the paths relative to the toplevel
    #   directory, not the current work directory.
    # - Use "--no-empty-directory" to avoid printing dirs that contain only
    #   ignored files.
    p = Popen(["git", "ls-files", "--exclude-standard", "-o", "--directory", "-z", "--full-name", "--no-empty-directory"],
              stdout=PIPE)
    stdout, _ = p.communicate()

    if p.returncode != 0:
        raise Exception("error here")

    return parse_z(stdout)


# :: void -> None or byte object (or raises an exception)
# TODO currently unused. Maybe remove this function
def git_get_toplevel():
    p = Popen(["git", "rev-parse", "--show-toplevel"], stdout=PIPE, stderr=DEVNULL)
    stdout, _ = p.communicate()
    if p.returncode == 0:
        return stdout.rstrip(b"\n")
    elif p.returncode == 128:
        # fatal: not a git repository (or any of the parent directories): .git
        return None
    else:
        # TODO Create a generic git error exception
        raise Exception("git failure")


# NOTE This is cwd aware
def git_clone(url, directory):
    p = Popen(["git", "clone", "-q", url, directory])
    p.communicate()
    if p.returncode != 0:
        raise Exception("git failure")


def git_reset_hard(sha1):
    p = Popen(["git", "reset", "-q", "--hard", sha1])
    p.communicate()
    if p.returncode != 0:
        raise Exception("git failure")


def is_sha1(sha1: bytes) -> bool:
    assert isinstance(sha1, bytes)
    if len(sha1) != 40:
        return False
    return all(0x30 <= c <= 0x39 or 0x61 <= c <= 0x66 for c in sha1)


# TODO Split this command. It seems like a ugly combination
def git_init_and_fetch(url: str, ref: bytes) -> bytes:
    p = Popen(["git", "init", "-q"])
    p.communicate()
    if p.returncode != 0:
        raise Exception("git failure")

    cmd = ["git", "fetch", "-q", url, ref]

    # NOTE: Http transport which is currently used in the tests! And for dump
    # the "--depth" argument does not work. So we need this hack for the tests.
    # The git error message is
    #     fatal: dumb http transport does not support shallow capabilities
    # TODO implement this hack nicly!
    # TODO No need for an env variable or argument. This code should
    # automatically detect whether shallow cloes are working or not!
    if os.environ.get("HACK_DISABLE_DEPTH_OPTIMIZATION", "0").strip() != "1":
        cmd += ["--depth", "1"]
    p = Popen(cmd, stderr=DEVNULL)
    # NOTE If stderr==DEVNULL(no-tty) no progress is showing on the commandline
    # Not getting the error is bad!
    p.communicate()
    if p.returncode != 0:
        # TODO think about error handling!!
        # Maybe every subcommand should be able and allows to write to stderr
        # directly!
        raise Exception("git failure: %d" % (p.returncode,))

    # get SHA1 of fetched object
    with open(".git/FETCH_HEAD", "br") as f:
        sha1 = f.read().split(b"\t", 1)[0]

    assert is_sha1(sha1)
    return sha1
