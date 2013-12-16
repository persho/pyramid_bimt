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

The ``pyramid_bimt`` package is not intended to be used as a standalone pyramid
application, but as a part of a "bimt app" -> a pyramid application, *using*
``pyramid_bimt`` as a base framework providing authentication, users, audit
log, etc.

So to develop the ``pyramid_bimt`` package, you first need to checkout an
app using it. As an example, let's use the BigMediaScraper (bms) app:

Prepare the environment::

    # fetch latest bms code
    $ git clone https://github.com/niteoweb/bms.git
    $ cd bms

    # build development environment
    $ make

    # now mark pyramid_bimt as a "development" egg: this will checkout the
    # source of pyramid_bimt into the src/pyramid-bimt folder of the bms app
    # and link it inside the bin/pserver script
    $ bin/develop checkout pyramid-bimt
    $ bin/buildout

Now you can run a variety of commands::

    # Start the development instance of Pyramid, with the local copy of bimt
    # code that is in src/pyramid-bimt
    $ bin/pserve etc/development.ini --reload

    # development commands
    $ cd src/pyramid-bimt
    $ make docs  # generate HTML format of docs for local viewing
    $ make tests  # run all tests
    $ make coverage  # generate HTML report of test coverage
    $ make clean  # clean up if something is broken and start from scratch


Release process
---------------

The ``pytamid_bimt`` package is hosted on our private PyPI at
https://pypi.niteoweb.com. New releases are made automatically by Travis CI
whenever a new tag is pushed to GitHub. To make a new release, run ``make
release``. This command will do the following:

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
    find-links += https://pypi.niteoweb.com/simple/
    allow-hosts += *pypi.niteoweb.com

    [basicauth]
    credentials = niteoweb-pypi
    interactive = no

    [niteoweb-pypi]
    uri = https://pypi.niteoweb.com/simple/
    username = niteoweb
    password = ni6kixe2why9ga

To use it in a pip ``requirements.txt`` file, add the following::

    -i https://niteoweb:ni6kixe2why9ga@pypi.niteoweb.com/simple
