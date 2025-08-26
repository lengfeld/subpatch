#!/bin/sh

(cd _build/html/ && find) | sort | cut -c 3- > sphinx.list

(git ls-tree --full-tree origin/gh-pages -r  | cut -c 54-) | sort > mkdocs.list
