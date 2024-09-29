# Basic usage

This tutorial explains how to add a third party dependency with subpatch to a
git repository.

In this tutorial the superproject is a simple C-library project that contains a
function that adds two numbers. The subproject (=third party dependency) is the
[GoogleTest](https://google.github.io/googletest/) test library for C and C++
projects.


## Prerequisites

To follow the tutorial you need the following setup

* Basic knowledge of git and the command line
* git installed
* subpatch installed (See [Installation](installation.md) for the details)
* (optional) cmake and a c/c++ compiler installed


## Cloning the example repository

First you need to clone the
[example repository](https://github.com/lengfeld/subpatch-example0). It's
the superproject that contains minimal C library. On the command line execute

    $ git clone https://github.com/lengfeld/subpatch-example0
    $ cd subpatch-example0

If interested, have a look at the `README.md` file.


## (optional) Buliding the C project

If you want, you can also build the C library and test the example program.
You need cmake and a c/c++ compiler for that. Execute the commands

    $ cmake -B build .
    $ cmake --build build
    $ build/prog 9 7
    16


## Adding the third party dependency

The example project contains the file `test.cc`. It is currently unused,
because the GoogleTest dependency is missing. You will add it shortly.

As a good practice you should add all third party dependencies in a subfolder
called `external`. To add the dependency execute the commands

    $ mkdir external
    $ cd external
    $ subpatch add https://github.com/google/googletest -r v1.15.2

The last command takes some seconds to execute. It downloads the git repository
and extract the files. It uses revision `v1.15.2` of the git repository. It's a
git tag that points to the current latest release of googletest.

When the command finishes it prints the message

    Adding subproject 'https://github.com/google/googletest' into 'googletest'... Done.
    - To inspect the changes, use `git status` and `git diff --staged`.
    - If you want to keep the changes, commit them with `git commit`.
    - If you want to revert the changes, execute `git reset --merge`.

The message contains three different options. To see what subpatch added
to the git index, execute

    $ git status

There are around 240 new files. Commit them by executing

    $ cd ..
    $ git commit -m "external: Adding GooglTest dependency"

Info: Apart from the files of the third party dependency subpatch also
adds some metadata to the superproject. You can find it a the root
directory of the git repository in the file `.subpatch`. For this
tutorial the content looks like

    [subpatch "external/googletest"]
    	url = https://github.com/google/googletest


## (optional) Enable and build the tests

After adding the GoogleTest dependency, you can build and execute the tests.
Open the `CMakeLists.txt` file and enable them. You can find the needed cmake
configuration already in the file, just remove the comments. Now the last lines
of the file should look like

    # Tests
    add_subdirectory(external/googletest gtest)
    add_executable(test test.cc)
    target_link_libraries(test GTest::gtest_main add)
    include(GoogleTest)
    gtest_discover_tests(test)

After that you can build and run the tests with

    $ cmake --build build
    $ build/test

Executing the last command will perform all tests and show the test results. All
tests should pass!


## Congratulations

Congratulations! You have added your first subproject with subpatch.
