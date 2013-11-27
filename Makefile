# convenience makefile to boostrap & run buildout
# use `make options=-v` to run buildout with extra options

python = python2.7
options =

all: docs tests

coverage: htmlcov/index.html

htmlcov/index.html: src/pyramid_bimt/*.py bin/coverage
	@bin/coverage run --source=./src/pyramid_bimt/ --branch bin/nosetests
	@bin/coverage html -i
	@touch $@
	@echo "Coverage report was generated at '$@'."

docs: docs/html/index.html

docs/html/index.html: README.rst docs/*.rst src/pyramid_bimt/*.py bin/sphinx-build
	@bin/sphinx-build -W docs docs/html
	@touch $@
	@echo "Documentation was generated at '$@'."

bin/sphinx-build: .installed.cfg
	@touch $@

db: .installed.cfg
	@if [ -f pyramid_bimt-app.db ]; then rm -rf pyramid_bimt-app.db; fi;
	@bin/py -m pyramid_bimt.scripts.populate

.installed.cfg: bin/buildout buildout.cfg buildout.d/*.cfg setup.py
	bin/buildout $(options)

bin/buildout: bin/python buildout.cfg bootstrap.py
	bin/python bootstrap.py
	@touch $@

bin/python:
	virtualenv -p $(python) --no-site-packages .
	@touch $@

tests: .installed.cfg
	@bin/flake8 setup.py
	@bin/code-analysis
	@bin/nosetests -s

release: .installed.cfg
	@bin/prerelease
	@VERSION=`python setup.py --version`; echo "Tagging version v$$VERSION"; git tag -a v$$VERSION -m "version $$VERSION"
	@bin/postrelease

clean:
	@rm -rf .coverage .installed.cfg .mr.developer.cfg .Python bin build \
		develop-eggs dist docs/html htmlcov lib include man parts \
		src/pyramid_bimt.egg-info pyramid_bimt-app.db

.PHONY: all docs tests clean