root_dir := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
bin_dir := $(root_dir)/ve/bin

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

all: devenv test

.PHONY: docs

devenv:	ve/bin/fullrelease

ve/bin/fullrelease:
	virtualenv ve
	$(bin_dir)/pip install -e .[test]

help: ## display this message
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

generate: ## generate environment for tests
	cd pyroma/testdata/complete;python setup.py sdist --formats=bztar,gztar,tar,zip
	cp pyroma/testdata/complete/dist/complete-1.0.dev1.* pyroma/testdata/distributions/

tests: devenv generate ## run tests
	tox -e py

clean: clean-pyc ## remove all

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name 'pip-selfcheck.json' -exec rm -fr {} +
	find . -name 'pyvenv.cfg' -exec rm -fr {} +
