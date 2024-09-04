# Introduction

This page should introduce you to the problem space of multi repository
management and third party source dependencies. It's not a common problem for
every software developers. The problem only arises when dealing for bigger
software products, inter team software dependencies and in embedded software
engineering.

This page explains the issue with two examples:

* Example 1: C/C++ library as source dependency
* Example 2: multi repository project for linux embedded firmware


## Example 1: C/C++ library as source dependency

This example illustrates a third party source dependency.

I publish a small C/C++ library
[aminilog](https://github.com/lengfeld/aminilog). It's useful when writing
C/C++ code in a Android Application project that uses the Android NDK (Native
Development toolkit). The library provides ready to use logging macros, so a
developer does need to write the logging macros for every NDK project from
scratch.

The library is only publish as a git repository. It's really simple. So there
are no releases or tags and no binary artifacts, too. Also binary artifacts
would do not make sense, because all of the library content are C/C++ Macros
that must be evaluated at compile time of the user of the header.

For a talk about the
[Glass-To-Glass-Latency in Android](https://www.youtube.com/watch?v=NKP4JcVegbY)
I made a lot of experiments on the Android platform and develop an Android
Application that could perform various tests. I published the code of the
application on github in the repo
[inovex/android-glass-to-glass-latency](https://github.com/inovex/android-glass-to-glass-latency/)

In this application I also used the Android NDK to write some C++ code to
access some libc functions from Java and to trigger the torch light of the
Pixel2 phone as fast as possible.

And while written and testing the C++ code I needed to write some log messages.
Therefore I imported my *aminilog* library as a source dependency into the
project. The commands were roughly the following:

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
