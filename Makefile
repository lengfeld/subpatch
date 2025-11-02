# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

all: subpatch.py

subpatch.py: src/util.py src/config.py src/git.py src/cache.py src/super.py src/main.py
	scripts/pybundle.py $^ > $@.tmp
	mv $@.tmp $@
	chmod +x $@

.PHONY: tests
tests:  subpatch.py    ### Runs the unit and integration tests
	python3 -m unittest discover -s tests
	TEST_BIN_PATH=$$PWD/subpatch.py tests/test_prog.py
	@# Also test executing the scripts by hand
	cd tests && for s in ./test_*.py; do $$s ; done

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
	ruff check src/*.py tests/*.py scripts/*.py
	@# Running pycodestyle again, because ruff does not check everything
	pycodestyle src/*.py scripts/*.py --max-line-length=140
	@# In the tests exclude the rule
	@#    E402 module level import not at top of file
	@#    W291 trailing whitespace
	@#    W293 blank line contains whitespace
	@# because the code needs it for the relative imports
	pycodestyle --ignore=E402,W291,W293 tests/*.py  --max-line-length=140


.PHONY: reformat
reformat:
	isort src/*.py tests/*.py scripts/*.py

.PHONY: dist
dist: subpatch.py
	rm -rf dist
	python3 -m build

.PHONY: clean
clean:
	rm -rf dist subpatch.py
	# Clean left over temp directories. Can happen when the test scripts
	# crash.
	find tests/ -maxdepth 1 -type d -name "Test*" -exec rm -fr "{}" \;

# see http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help: ## Show the help prompt
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


src-files-graph.png: src-files-graph.dot
	dot -Tpng $< -o $@
