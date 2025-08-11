#!/bin/sh
#
# This script is nearly the same as the
#    https://subpatch.net/tut/basic-usage/
# tutorial. It's useful to test the commands and the output
#
# TODO Integrate this into a test framework. The commands and the output in
# the documentation/website should be tested against the latest version of
# subpatch.

set -x
set -e

# TOOD make the clone
#

git reset --hard origin/main
rm -rf build/


cmake -B build .
cmake --build build

build/prog 9 7
# TODO check output

mkdir external
cd external
subpatch add https://github.com/google/googletest -r v1.15.2
# Check output message

# git status

cd ..
git commit -m "external: adding gtest"

subpatch status

cat >> CMakeLists.txt <<EOF
add_subdirectory(external/googletest gtest)
add_executable(test test.cc)
target_link_libraries(test GTest::gtest_main add)
include(GoogleTest)
gtest_discover_tests(test)
EOF

cmake --build build
build/test

git add CMakeLists.txt
git commit -m "enable tests"


subpatch update external/googletest -r v1.17.0

cmake --build build
build/test


git commit -m "external: update gtest"

subpatch status

git log --format=%s
