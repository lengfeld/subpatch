# Installation

This tutorial explains who to install subpatch on your computer. Currently
there are two ways to install subpatch:

1. With [pipx](https://pipx.pypa.io/stable/) into your HOME directory
2. As a standalone script into the PATH

**Warning**: subpatch is in a very *very* early stage. Do not use it in
production environments! E.g. the config format will change. Nevertheless
please try it out. Any feedback is welcome.


## Prerequisites

To follow this tutorial you need a PC or notebook with a Linux Operating
System installed. This tutorial will assume [Ubuntu](https://ubuntu.com/), but
any current distribution should work. Also MacOS may work out of the box, but
it's not tested for now.


## With pipx into your HOME directory

The subpatch project is released on [PyPI](https://pypi.org/), the "Python
Package Index". The [PyPI's subpatch site](https://pypi.org/project/subpatch/)
contains the project specific informations.


### Install pipx

To install subpatch, you can use [pipx](https://pipx.pypa.io/). pipx is a tool
to manage [python virtual
environments](https://docs.python.org/3/tutorial/venv.html) in your HOME
directory.

To install pipx on Ubuntu, execute

    $ sudo apt install pipx

*Note*: For other distributions use the distro specific package manager.

To check if pipx works, you can execute the `list` command. An example:

    $ pipx list
    nothing has been installed with pipx 😴


### Install subpatch with pipx

If everything is fine, you can install the latest version of subpatch with the command

    $ pipx install subpatch

The output of the command should look like

      installed package subpatch 0.1a2, installed using Python 3.10.12
      These apps are now globally available
        - subpatch
    done! ✨ 🌟 ✨

If some of the numbers are different, that's o.k.

To test that subpatch works, you can execute the command

    $ subpatch --version

It should print the version number of subpatch that is currently installed.

**Congratulations**, now you successfully installed subpatch. A final note: To
get further infos and the help text, execute

    $ subpatch --help


## As a standalone script into the PATH

You can also install subpatch as a standalone python script into your PATH.


### Create a `bin` folder

First make sure that you have a directory that is listed in your PATH. If you
have another folder in the PATH for other scripts already, you can skip this
step.

I used a `bin` directory in the HOME folder for that. To create it, execute

    $ mkdir ~/bin

Then this folder must be added to the environment variable PATH. This can be
done with

    $ echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc

It adds a line at the end of the `~./bashrc` file.

The change will only be active in new shells that are spawned now. So start a new shell with

    $ bash

*Note*: This tutorial assumes that you are using bash. If you use another
shell, like zsh or fish, you mostly already know everything in the tutorial and
can adapt it yourself :-)

To check that the modifications of the PATH variable worked, execute

    $ echo $PATH

It prints all folders that are scanned for executable files. The list should
contain the `bin` folder in your HOME directory at the end.


### Download and install subpatch

The last step is to download the subpatch script and copy it into the `bin` folder.

First go to the [releases page](../ref/releases.md) and find the latest
release. There are two options: manual download or using the command line:

#### Manual download

Now click on the link for *standalone python script* and download the script
with your browser.

After you downloaded the standalone script into your download directory, you
must move it to the `bin` directory. For example:

    $ mv subpatch ~/bin/

The executable bit is not set for downloaded files. You must manually set it
with the command

    $ chmod +x ~/bin/subpatch

Otherwise the shell cannot execute the script.


#### Using the command line

Apart from the manual download, you can use command line tools. To download
the script and set the executable bit, just execute:

    $ wget https://github.com/lengfeld/subpatch/releases/download/v0.1a2/subpatch -O ~/bin/subpatch
    $ chmod +x ~/bin/subpatch

The above command is just an example. For other versions of subpatch, the
version number in the URL looks different.


### Test subpatch

After download and installation you should test the subpatch command line tool.
To test that it works, you can execute the command

    $ subpatch --version

It should print the version number of subpatch that is currently installed.

**Congratulations**, now you successfully installed subpatch. A final note: To
get further infos and the help text, execute

    $ subpatch --help
