# Project based on Yocto

This how-to guide explains how to use subpatch to maintain an embedded Linux
firmware based on the [Yocto project](https://yoctoproject.org/).

A full feature example of a Yocto project maintained with subpatch is available
here: [yocto-example](https://github.com/subpatch/example-yocto)

Note: There are maybe some mistakes in the following commands. There are no
automated tests yet.


## Prerequisites

This how-to guide is not a tutorial. You should have install subpatch already
and learned the basic usage of subpatch. If not, please work trough the
tutorials.

The preconditions are

* subpatch installed
* Basic usage of subpatch known
* Basic usage of Yocto known


## Adding poky

First you need add the [poky](https://git.yoctoproject.org/poky/) repository.
This how-to guide adds all layers in a sub directory called `sources`. You may
also just add the repos at the toplevel directory.

This guide uses a fresh git repository, but you can also use a existing one.
Execute:

    $ git init
    $ mkdir sources
    $ cd sources
    $ subpatch add https://git.yoctoproject.org/poky -r scarthgap
    $ git commit -m "adding poky"

The above commands add poky from the branch `scarthgap` into the directory
`sources/poky/`. At the time of writing, this branch is the latest long term
support branch. See
[Releases](https://wiki.yoctoproject.org/wiki/Releases) on the Yocto wiki for
more details.

Now you can already initialize the build environment:

    $ cd ..
    $ . sources/poky/oe-init-build-env

This will create a `build` directory with the default configurations for
local.conf and bblayers.conf


## Adding additional layers

To find recipes and layers you can use the
[OpenEmbedded Layer Index](https://layers.openembedded.org).
When you want to add a layer, you use subpatch's `add` command .

The following example adds the git repository `meta-openembedded` that contains
multiple layers:

    # Starting in the `build/` subdirectory
    $ cd ../sources
    $ subpatch add git://git.openembedded.org/meta-openembedded -r scarthgap
    $ git commit -m "add meta-openembedded"

subpatch adds all files of the layer in the directory
`sources/meta-openembedded`.  After that, you can update your bblayers.conf to
include the new layer(s).

    $ cd ../build
    $ bitbake-layers add-layer ../meta-openembedded/meta-oe
    $ bitbake-layers add-layer ../meta-openembedded/meta-python

Repeat this for all external layers you want to add.


## Adding your own layer

To maintain your local recipes, bbappends, distro and default build
configuration it's good to add your own layer.

This example calls the layer `mylayer` and places it next to `poky` into the
`sources/` subdirectory.

    # Starting in the `build/` subdirectory
    $ bitbake-layers create-layer ../sources/meta-mylayer

Don't forget to add this layer to your bblayers.conf and to commit your changes

    $ bitbake-layers add-layer ../sources/meta-mylayer
    $ git add ../sources/meta-mylayer
    $ git commit -m "add mylayer"

See

* [Understanding and Creating Layers](https://docs.yoctoproject.org/dev/dev-manual/layers.html#understanding-and-creating-layers) and
* [Creating a new BSP Layer Using the bitbake-layers Script](https://docs.yoctoproject.org/dev/bsp-guide/bsp.html#creating-a-new-bsp-layer-using-the-bitbake-layers-script)

in the official Yocto documentation for further details.


## Adding default build configuration

To share your local.conf and bblayers.conf with other developers, you can store
a default local.conf and bblayers.conf in our own layer.

    # Starting in the `build/` subdirectory
    $ bitbake-layers save-build-conf ../sources/meta-mylayer/ myconf

The above command stores the template config in the directory
`sources/meta-mylayer/conf/templates/myconf/`. To share it with other
developers also commit it:

    $ git add ../sources/meta-mylayer/conf/templates/myconf/
    $ git commit -m "add my template"

New developers can use the following command to initialized their build
configuration from the template after a fresh checkout of the superproject.

    $ TEMPLATECONF=../meta-mylayer/conf/templates/myconf . sources/poky/oe-init-build-env

See [Creating a Custom Template Configuration Directory](https://docs.yoctoproject.org/next/dev-manual/custom-template-configuration-directory.html)
in the official Yocto Documentation for more details.


## Updating layers to a new stable release

From time to time you should update the subprojects (= the Yocto layers and
poky) to the newest stable version. For Yocto layers it means to update
to the newest commit on the specific stable branch.  For that you can use
subpatch's `update` command.

First get an overview of all the subprojects (=layers and poky in this how-to)
the superproject uses:

     # In the toplevel directory
     $ subpatch list

     # and for more information about the subprojects
     $ subpatch status

Then you can update every layer one by one.

     $ subpatch update sources/poky
     $ git commit -m "updating poky"

     $ subpatch update sources/meta-openembedded
     $ git commit -m "updating meta-openembedded

Before publishing your changes for review, you should make a local build and
run some smoke tests of course.

*Note 1*: For now subpatch does not have a `foreach` command. So you need to
update every layer separately.

*Note 2*: For now subpatch does not have a `update --dry-run` command. So just
checking for updates means downloading the remote repository. subpatch already
uses `--depth 1`, but it can be a expensive network operation nevertheless.


## How to make a release

If you want to make a release of your firmware, you can just tag the
superproject like any project that is using git. Of course your project setup
may need additional steps, e.g. updating a version number or adding release
notes.

But since subpatch is only an addition to git, you can use the standard git
workflow for releasing. Some example commands:

    # Increase version number
    $ vim sources/meta-mylayer/ TODO add file here
    $ git commit -a -m "Makeing release vX.Y"
    $ git tag -m "release vX.Y vX.Y
    $ git push --follow-tags --dry-run
    $ git push --follow-tags


## Upgrading to a new release branch

To update all layers to a new release branch, e.g., from `scarthgap` to
`styhead`, you can also use subpatch's `update` command.

First execute

    $ subpatch status

It will list all subprojects with additional information, e.g. the upstream
branch that the subproject uses.

You can update to a new release branch with

    $ subpatch update sources/poky -r styhead
    $ subpatch update sources/meta-openembedded -r styhead
    $ git commit -m "upgrade to new release branch"

In all cases this major upgrade requires additional changes in your layer and
additional testing.
