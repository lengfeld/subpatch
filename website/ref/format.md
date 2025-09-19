# Configuration and metadata format

The subpatch configuration file and the metdata files use the git config file
format.

## Configuration

A superproject contains a subpatch configuration file. It's call `.subpatch`
and place at the toplevel directory of the superproject. In the case of git
it's placed next to the `.git` folder.

Example configuration file:

    [subprojects]
        path = dirA
        path = dirB

For now there is only one section:

* `[subprojects]`
    * `path`: Path to the subproject from the toplevel directory of the superproject.
       For every subproject there is a seperate `path` value.

## Metadata

Every subproject as a metadata file. It's called `.subproject` and place at the
top level directory of the subproject.

Example metadata file:

    [patches]
        appliedIndex = -1
    [subtree]
         checksum = 202864b6621f6ed6b9e81e558a05e02264b665f3
    [upstream]
        objectId = c4bcf3c2597415b0d6db56dbdd4fc03b685f0f4c
        rev = refs/heads/master
        url = ../subproject TODO add real url

There are different sections and every section as different keys:

* `[upstream]`
    * `url`: URL of remote git repository
    * `rev`: git revision that is integrated, e.g. `HEAD`, `refs/heads/master` or `v1.0`
    * `objectId`: The SHA1 of the git object that is integrated.
* `[patches]`
    * `appliedIndex`: Integer from -1 to count of patches minus 1
* `[subtree]`
    * `checksum`: A checksum over the subproject's files after integration (and before patches are applied).
