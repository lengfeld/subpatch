# Basic usage

This tutorial explains how to add a third party dependency to a git repository.
You will learn

* how to add a subproject to the superproject,
* how to query the subprojects and get more information about them and
* how to upgrade a subproject to a new upstream version.

In this tutorial the superproject is a simple C-library project that contains a
single function that adds two numbers. The subproject (=third party dependency)
is the [GoogleTest](https://google.github.io/googletest/) test library for C
and C++ projects.


## Prerequisites

To follow the tutorial you need the following setup and skills:

* Basic knowledge of git and the command line
* git installed
* subpatch installed (See [Installation](installation.md) for the details)
* (optional) cmake and a c/c++ compiler installed


## Cloning the example repository

First you need to clone the
[example repository](https://github.com/subpatch/tutorial-basic-usage). It's
the superproject that contains minimal C library. On the command line execute

    $ git clone https://github.com/subpatch/tutorial-basic-usage
    $ cd tutorial-basic-usage

If interested, have a look at the `README.md` file.


## (optional) Building the C project

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
git tag that points to the current latest release of GoogleTest.

When the command finishes it prints the message

    Adding subproject 'googletest' from URL 'https://github.com/google/googletest' at revision 'v1.15.2'... Done.
    - To inspect the changes, use `git status` and `git diff --staged`.
    - If you want to keep the changes, commit them with `git commit`.
    - If you want to revert the changes, execute `git reset --merge`.

The message contains three different options. To see what subpatch added
to the git index, execute

    $ git status

There are around 240 new files. Commit them by executing

    $ cd ..
    $ git commit -m "external: add gtest"

You have added your first subproject. To see all subprojects execute

    $ subpatch list
    external/googletest

For now there is only a single subproject. To see more details about the
subprojects use the `status` command.

    $ subpatch status
    NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
    NOTE: The format is markdown currently. Will mostly change in the future.

    # subproject at 'external/googletest'

    * was integrated from URL: https://github.com/google/googletest
    * has integrated revision: v1.17.0
    * has integrated object id: 52eb8108c5bdec04579160ae17225d66034bd723


## (optional) Enable and build the tests

After adding the GoogleTest dependency, you can build and execute the tests.
Open the `CMakeLists.txt` file and add the following lines at the end:

    # Tests
    add_subdirectory(external/googletest gtest)
    add_executable(test test.cc)
    target_link_libraries(test GTest::gtest_main add)
    include(GoogleTest)
    gtest_discover_tests(test)

After that you can build and run the tests with

    $ cmake --build build
    $ build/test

Executing the last command will perform all tests and show the test results.
All tests should pass!

Don't forget to commit the changes to the `CMakeLists.txt`:

    $ git add CMakeLists.txt
    $ git commit -m "enable tests"


## Updating the subproject

There is a new version of GoogleTest available already. See the
[releases page on github](https://github.com/google/googletest/releases). So update the
subproject to a new version.

     $ subpatch update external/googletest -r v1.17.0

This will print the output

    Updating subproject 'external/googletest' from URL 'https://github.com/google/googletest' to revision 'v1.17.0'... Done.
    - To inspect the changes, use `git status` and `git diff --staged`.
    - If you want to keep the changes, commit them with `git commit`.
    - If you want to revert the changes, execute `git reset --merge`.


## (optional) Retest after update

After the update of a dependency you should retest your project. For this
tutorial it's optional, but it's not optional for a real world project.

Execute the tests with

    $ cmake --build build
    $ build/test


## Finish the update

After the update all tests are still o.k. Since you are confident of the version upgrade now,
commit the changes with

    $ git commit -m "external: update gtest"

After commit `subpatch status` prints the new information:

    $ subpatch status
    NOTE: The format of the output is human-readable and unstable. Do not use in scripts!
    NOTE: The format is markdown currently. Will mostly change in the future.

    # subproject at 'external/googletest'

    * was integrated from URL: https://github.com/google/googletest
    * has integrated revision: v1.17.0
    * has integrated object id: 52eb8108c5bdec04579160ae17225d66034bd723


## Conclusion

Congratulations! You have

* added your first subproject to a superproject with `subpatch add`,
* queried information with `subpatch list` and `subpatch status ` and
* updated the subproject to a new upstream version with `subpatch update`.

Now you are ready to continue with the next tutorial [Applying patches](applying-patches.md).
