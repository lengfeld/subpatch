# subpatch's wobsite

This is the source of the website [subpatch.net](https://subpatch.net).
It's generate with [sphinx](https://www.sphinx-doc.org/en/master/)
and uses the
[Read the Docs Sphinx Theme](https://sphinx-rtd-theme.readthedocs.io/en/stable/index.html).


## Prepare build environment

To install sphinx, tools and the theme, you can use:

    $ python -m venv venv
    $ . venv/bin/activate
    $ pip install sphinx
    $ pip install myst-parser
    $ pip install sphinx-rtd-theme


## Building and publish

To build the website locally, execute:

    $ . venv/bin/activate
    $ cd website
    $ make html

To show the result, execute

    $ browse _build/html/index.html

To deploy, execute:

    TODO


# Background

The structure of the website/documentation is based on
[The Grand Unified Theory of Documentation](https://docs.divio.com/documentation-system/).
It structures documentation into four categories:

* explanations
* tutorials
* how-to guides
* reference


# Conventions

The term 'subpatch' is always spelled lowercase. Even at the start of sentence.
