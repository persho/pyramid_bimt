# convenience makefile to boostrap & run buildout
# use `make options=-v` to run buildout with extra options

python = python2.7
options =

all: docs tests

docs: docs/html/index.html

docs/html/index.html: README.rst docs/*.rst src/pyramid_bimt/*.py bin/sphinx-build
	@bin/sphinx-build -W docs docs/html
	@touch $@
	@echo "Documentation was generated at '$@'."

bin/sphinx-build: .installed.cfg
	@touch $@

.installed.cfg: bin/buildout buildout.cfg buildout.d/*.cfg setup.py
	bin/buildout $(options)

bin/buildout: bin/python buildout.cfg bootstrap.py
	bin/python bootstrap.py
	@touch $@

bin/python:
	virtualenv -p $(python) --no-site-packages .
	@touch $@

tests: .installed.cfg
	@bin/nosetests --with-coverage --cover-package=pyramid_bimt \
		--cover-min-percentage=100 --cover-html
	@bin/flake8 setup.py
	@bin/code-analysis

release: .installed.cfg
	@bin/prerelease
	@VERSION=`python setup.py --version`; echo "Tagging version v$$VERSION"; \
		git tag -a v$$VERSION -m "version $$VERSION"
	@bin/postrelease

graphviz: .installed.cfg
	@bin/py bin/SA_to_dot.py
	@dot -Tpng /tmp/schema.dot > docs/images/schema.png
	@echo "Graphviz image generated at 'docs/images/schema.png'."

clean:
	@rm -rf .coverage .installed.cfg .mr.developer.cfg .Python bin build \
		develop-eggs dist docs/html cover lib include man parts \
		src/pyramid_bimt.egg-info

.PHONY: all docs tests clean
