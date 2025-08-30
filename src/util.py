from enum import Enum
import contextlib
import os


class URLTypes(Enum):
    LOCAL_RELATIVE = 1
    LOCAL_ABSOLUTE = 2
    REMOTE = 3


def get_url_type(url):
    if len(url) == 0:
        raise ValueError("The URL is empty!")

    # TODO mabye using url parsing library?
    # TODO Implemente "file://" prefix
    if url.startswith("http"):
        return URLTypes.REMOTE
    elif url.startswith("git"):
        return URLTypes.REMOTE
    elif url.startswith("ssh"):
        return URLTypes.REMOTE
    if "://" in url:
        raise NotImplementedError("The URL '%s' is not implemented yet" % (url,))

    # Is mostly just a local path
    if url[0] == "/":
        return URLTypes.LOCAL_ABSOLUTE

    return URLTypes.LOCAL_RELATIVE


# TODO Use https://docs.python.org/3/library/contextlib.html#contextlib.chdir
# TODO copied from helpers. Unify!
@contextlib.contextmanager
def cwd(path, create=False):
    if create:
        os.makedirs(path)
    old_path = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_path)


# TODO Write blogpost about common error categories, e.g. in HTTP and errno
# E.g. there is also
#  * invalid argument/Bad request
#  * (generic) runtime error (maybe the same as IO error)
#  * permission denied
#  * NotImplemented/Does not exists
class ErrorCode(Enum):
    UNKNOWN = 1
    # TODO distinguish between "not implemented" and "not implemented __yet__"!
    # Not implemented should mostly be a invalid argument then
    NOT_IMPLEMENTED_YET = 2
    SUPERPROJECT_NOT_FOUND = 3  # if no scm system found and no config found
    SUPERPROJECT_NOT_CONFIGURED = 4
    # The user has given an invalid argument on the command line
    INVALID_ARGUMENT = 5
    # TODO remove this type. Every ErrorCode should support a message.
    CUSTOM = 6


class AppException(Exception):
    def __init__(self, code, msg=None):
        self._code = code
        if msg is not None:
            super().__init__(msg)
        else:
            super().__init__()

    def get_code(self):
        return self._code
