# Configuration and metadata format

The subpatch configuration file and the metadata files use the git config file
format.


## Configuration

A superproject contains a subpatch configuration file. It's call `.subpatch`
and place at the toplevel directory of the superproject. In the case of git
it's placed next to the `.git` folder.

Example configuration file:

    [subprojects]
            path = sources/meta-openembedded
            path = sources/meta-raspberrypi
            path = sources/poky

For now there is only one section:

* `[subprojects]`
    * `path`: Path to the subproject from the toplevel directory of the superproject.
       For every subproject there is a separate `path` value.


## Metadata

Every subproject as a metadata file. It's called `.subproject` and place at the
top level directory of the subproject.

Example metadata file:

    [subtree]
            appliedIndex = 0
            checksum = d35979e585e180a212a2eb1eedb71cb0ea53542b
    [upstream]
            objectId = af3049cec7c916d96cf8214c6f9ae77710f667db
            revision = refs/heads/master
            url = https://github.com/lengfeld/live555-unofficial-git-archive.git

There are different sections and every section as different keys:

* `[upstream]`
    * `url`: URL of remote git repository
    * `revision`: git revision that is integrated, e.g. `HEAD`, `refs/heads/master` or `v1.0`
    * `objectId`: The SHA1 of the git object that is integrated.
* `[patches]`
    * This section contains no value yet
* `[subtree]`
    * `checksum`: A checksum over the subproject's files after integration (and before patches are applied).
       If the subtree is unpopulated, no value is present.
    * `appliedIndex`: Integer from -1 to count of patches minus 1 (default value is -1)
