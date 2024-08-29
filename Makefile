# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

all:

.PHONY: tests
tests:       ### Runs the python unit tests
	python3 -m unittest discover -s tests
	@# Also test executing the scripts by hand
	tests/test_lib.py
	tests/test_prog.py
	cd tests && ./test_lib.py && ./test_prog.py


# for README.md, TODO.md and CHANGELOG.md
%.html: %.md
	pandoc --toc -s $< > $@


.PHONY: lint
lint:                 ### Runs the pycodestyle on source code
	pycodestyle subpatch *.py tests/*.py


.PHONY: dist
dist:
	rm -rf dist
	python3 -m build

.PHONY: clean
clean:
	rm -rf dist

# see http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help: ## Show the help prompt
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
