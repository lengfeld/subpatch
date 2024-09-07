# Introduction

Welcome to the realm of multi-repository management and third-party source
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

TODO add example

## Recap

TODO write recap
