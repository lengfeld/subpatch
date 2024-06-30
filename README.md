# subpatch - subprojects done right!

subpatch is currently only an idea, but based on proven concepts.
See the website [subpatch.net](https://subpatch.net) for more details.

If you are interested create a github issue or email
[me](mailto:stefan+subpatch@lengfeld.xyz).

This project is licensed under the terms of the GPLv2 or later license.


## How to develop?

Useful makefile targets

    $ make tests
    $ make lint

How to execute a single tests

    $ python3 tests/test_main.py TestNoCommands.testVersion
    $ tests/test_main.py TestNoCommands.testVersion


## License - full disclaimer

Copyright (C) 2024 Stefan Lengfeld

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


## How to release

testing creating a release

    $ make dist
    $ twine upload --repository testpypi dist/*

How to test install

    $ pipx install --index-url https://test.pypi.org/simple/ subpatch



## TODOs

Start using pylint

Allow to lock subprojects. The CI check should error/warn, when a PR/commit
introduces changes to a subproject dir!
If a subroject is not locked, the CI would also error/warn and request the
contributer to execute a command to create a patch file!

Write test that
  $ git config -f .subpatch  subpatch."external/subpatch-website".url
works and add documentation.
This was found while reading some "git submodules" docu

Provide script to convert a
* kas
* git submodule (support recursion)
* repo
superproject to subpatch

Watch stackoverflow and respone to questions. (When the software is live.)

Text gui frontend for the layer index
(https://layers.openembedded.org/layerindex/branch/master/layers/)
to easily select and add layers to your yocto build. Replacement for kas.

Add how-to use subpatch with kas for a Yocto project

Add how-to use subpatch for Yocto project

Add how-to use subpatch for Zeyphr project

Integrated manpage into tool. Otherwise a single file install has no manpage!

Strip ".git" from URL after cloning. Should not happen

   $ subpatch  add https://github.com/google/googletest.git
   Adding subproject 'googletest.git' was successful.

Unify slogan/subtitle. fearless vs done-right

Show software/license disclaimer at more locations.
