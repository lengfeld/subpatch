# Introduction

Welcome to the realm of multi repository management and third-party source
dependencies. Even if you are an experienced software developer, you may not
have encountered this issue in your career already.  It only arises when
working on larger software projects, managing inter-team software dependencies,
or in the field of embedded software engineering.

This page explains the issue with two examples:

* Example 1: C/C++ library as source dependency
* Example 2: multi repository project for linux embedded firmware


## Example 1: C/C++ library as source dependency

This example illustrates a third party source dependency.

I maintain a small C/C++ library called
[aminilog](https://github.com/lengfeld/aminilog). It's useful when writing
C/C++ code in an Android Application project that uses the
[Android NDK](https://developer.android.com/ndk/)
(Native Development toolkit). The library provides ready to use logging macros,
because the NDK only contains the low level APIs for logging.

I publish the library as a plain git repository. Since it is really
simple, there are no release tarballs or tags and no binary artifacts. Also
binary artifacts would do not make sense, because all of the library content
are C/C++ macros that must be evaluated at compile time.

In 2023 I prepared a talk about the
[Glass-To-Glass-Latency in Android](https://www.youtube.com/watch?v=NKP4JcVegbY).
For my latency experiments I created a git repository and needed the above
mentioned C/C++ library as a source dependency.  I develop an Android
Application that could perform various tests and experiments. The code of the
application is on github in the repo
[inovex/android-glass-to-glass-latency](https://github.com/inovex/android-glass-to-glass-latency/).

In this application I also used the Android NDK to write some C++ code to
access some libc functions from Java and to trigger the torch light of the
Pixel2 phone as fast as possible.  And while written and testing the C++ code I
needed to write some log messages.  Therefore I imported my aminilog library as
a source dependency into the project. The commands were roughly the following:

    $ mkdir external/
    $ cd external/
    $ git clone https://github.com/lengfeld/aminilog.git
    $ rm -rf aminilog/.git
    $ git add aminilog/
    $ git commit -m "add aminilog dependency"

And then I integrated the library into the cmake build systems by adding the line

    add_subdirectory(../../../../pixeltorch pixeltorch)
    [...]
    target_link_libraries(${PROJECT_NAME} android [...] aminilog)

into the `CMakeLists.txt`.

That was all. I added the source files of the [aminilog](https://github.com/lengfeld/aminilog)
library as files to the git repository
[android-glass-to-glass-latency](https://github.com/inovex/android-glass-to-glass-latency/)
and integrated them to the cmake build system.
In this example the git repository *android-glass-to-glass-latency* is the
superproject and the source dependency *aminilog* is the subproject.


## Example 2: Embedded Linux firmware based on Yocto

This example illustrates a multi repository setup of a Yocto project.
The [Yocto project](https://yoctoproject.org) is a build system to build
a Linux embedded distribution and firmware. It's based on OpenEmbedded.

The core consists of

* bitbake (recipe parser and build orchestration)
* meta-oecore (base recipes and toolchain)
* documentation
* the poky distro

All of this is bundled in the [poky repository](https://git.yoctoproject.org/poky/).
Poky is often used as a based for embedded Linux firmware projects, but you can
also add the different components separately.

Furthermore the Yocto project has the concept of layers. These are git repositories
by external parties that contains additional recipes, bbappends, machines and
distros. These add additional hardware support, software and other features.
E.g. [meta-qt](https://github.com/meta-qt5/meta-qt5)
adds support for the QT graphics framework and
[meta-raspperypi](https://git.yoctoproject.org/meta-raspberrypi/about/) adds
support for the RaspberryPI hardware.

In general building an embedded firmware with Yocto consists of using poky and
2 or more additional external layers. And mostly also maintaining your own
layer with build configurations, additional patches and recipes for your own
applications.

As a developer you would clone multiple repositories . An
example:

    $ git clone https://git.yoctoproject.org/poky
    $ git clone git://git.openembedded.org/meta-openembedded
    $ git clone https://git.yoctoproject.org/meta-raspberrypi

Then you would configure the build and add the layers.

    $ . poky/oe-init-build-env
    $ vim conf/bblayers.conf
    $ vim conf/local.conf
    $ bitbake some-image

Then adding our own layer for your modifications:

    $ bitbake-layers create-layer ../meta-mylayer
    $ cd ../meta-mylayer
    $ git init
    # e.g. add an image recipe
    $ git commit -m "add image reipce"

And finally you start the build

    $ bitbake my-image

and use the firmware files in the build artifacts to flash your device.

This is also an example of a *multi repository management* problem.  To make a
firmware build for the device you, a coworker and the continuous integration
pipeline needs to clone four different repositories, namely

* poky,
* meta-openembedded,
* meta-raspperypi and
* meta-mylayer.

The first three repos are maintained by external parties. The last repo is
maintained by you.

Since everyone is facing the multi repository problem when working on Yocto
projects, there are already some attempts to handle it. E.g. some use
[repo](https://gerrit.googlesource.com/git-repo/+/HEAD/README.md) or
[git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
as generic solutions to the multi repository problem.  But
there is also the [kas](https://kas.readthedocs.io/en/latest/intro.html)
project.  It allows to checkout multi external git repos and provides a lot
additional feature for maintaining Yocto projects. E.g. to assemble the
`local.conf` and `bblayers.conf` dynamically.


## Recap

The two examples show the multi repository problem. Now you can continue
reading my [learnings and history](learnings.md) of the past years dealing with
this problem.
