Local development
=================

Prerequisites
-------------

* GCC, make, and similar (``apt-get install build-essential``)
* PostgreSQL development headers (``apt-get install libpq-dev``)
* Python 2.7 with development headers (``apt-get install python-dev``)
* virtualenv (``apt-get install python-virtualenv``)
* pip (``apt-get install python-pip``)
* git (``apt-get install git``)
* Node Package Manager (``apt-get install npm``)
* jshint (``npm install jshint -g``)

Code style guide
----------------

We follow `plone.api's style guide
<http://ploneapi.readthedocs.org/en/latest/contribute/conventions.html>`_. Read
it & use it.


Setting up a local development environment
------------------------------------------

Prepare the environment::

    # fetch latest code
    $ git clone https://github.com/niteoweb/pyramid_bimt.git
    $ cd pyramid_bimt

    # build development environment
    $ make

Now you can run a variety of commands::

    # if your DB is empty, populate it with demo content
    $ make db

    # Start the development instance of Pyramid
    $ bin/pserve etc/development.ini --reload

    # development commands
    $ make docs  # generate HTML format of docs for local viewing
    $ make tests  # run all tests
    $ make coverage  # generate HTML report of test coverage
    $ make clean  # clean up if something is broken and start from scratch


Release process
---------------

The ``pytamid_bimt`` package is hosted on our private PyPI at
http://niteoweb-pypi.herokuapp.com/packages/. New releases are made automatically
by Travis CI whenever a new tag is pushed to GitHub. To make a new release,
run ``make release``. This command will do the following:

#. Ask you for a version number for this release, update setup.py/CHANGELOG.rst
   with it and offer to commit the version change to git.
#. Create a git tag with the name 'v{$VERSION}'.
#. Ask you for a version number for the next release and append ``.dev0`` to it
   to indicate it's in development. It will again update setup.py/CHANGELOR.rst
   and offer to commit changes.
#. Offer to push both commits and the new tag.
#. Travis CI will build the tag and deploy the new release to our internal
   PyPI.


To use releases from our private PyPI in your project, you need to add the
following to your buildout::

    [buildout]
    extensions += isotoma.buildout.basicauth
    find-links += find-links += http://niteoweb-pypi.herokuapp.com/packages/
    allow-hosts += *@niteoweb-pypi.herokuapp.com

    [basicauth]
    credentials = niteoweb-pypi
    interactive = no

    [niteoweb-pypi]
    uri = http://niteoweb-pypi.herokuapp.com/packages/
    username = niteoweb
    password = ni6kixe2why9ga
