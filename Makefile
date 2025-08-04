# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

all:

.PHONY: tests
tests:       ### Runs the unit and integration tests
	python3 -m unittest discover -s tests
	@# Also test executing the scripts by hand
	tests/test_git.py
	tests/test_lib.py
	tests/test_prog.py
	tests/test_submodule.py
	cd tests && ./test_git.py && ./test_lib.py && ./test_prog.py && ./test_submodule.py

# The file website/index.md is nearly a one-to-one copy of the README.md file.
# But there are some differences for links and text. This check should verify
# that both files are in sync expect the expected references.
.PHONY: check-index-md
check-index-md:
	@# NOTE: "git diff" returns with 1 if there are changes. And changes are expected
	git diff --no-index README.md website/index.md > index.md.diff || true
	diff index.md.diff tests/index.md.diff
	rm index.md.diff
	@echo Everything is fine!

# For now just hook this up to the "lint" target.
lint: check-index-md


# for README.md, TODO.md and CHANGELOG.md
%.html: %.md
	pandoc --toc -s $< > $@


.PHONY: lint
lint:                 ### Runs linters (ruff, self-made) on the source code
	ruff check *.py tests/*.py

.PHONY: reformat
reformat:
	isort *.py tests/*.py

.PHONY: dist
dist:
	rm -rf dist
	python3 -m build

.PHONY: clean
clean:
	rm -rf dist
	# Clean left over temp directories. Can happen when the test scripts
	# crash.
	find tests/ -maxdepth 1 -type d -name "Test*" -exec rm -fr "{}" \;


# see http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help: ## Show the help prompt
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
