Local development
=================

Prerequisites
-------------

* GCC, make, and similar (``apt-get install build-essential``)
* PostgreSQL development headers (``apt-get install libpq-dev``)
* SQLite database browser (``apt-get install sqlitebrowser``)
* Python 2.7 with development headers (``apt-get install python-dev``)
* virtualenv (``apt-get install python-virtualenv``)
* pip (``apt-get install python-pip``)
* git (``apt-get install git``)


.. _setting-up-a-local-development-environment:

Setup up a local development environment
----------------------------------------

Prepare the environment:

.. code-block:: bash

    # fetch latest code
    $ git clone https://github.com/niteoweb/<APP>.git
    $ cd <APP>

    # build development environment
    $ make

Now you can run a variety of commands:

.. code-block:: bash

    # if your DB is empty, populate it with demo content
    $ make db

    # Start the development instance of Pyramid
    $ bin/pserve etc/development.ini --reload

    # development commands
    $ make docs  # generate HTML format of docs for local viewing
    $ make tests  # run all tests
    $ make coverage  # generate HTML report of test coverage
    $ make clean  # clean up if something is broken and start from scratch

Developing the ``pyramid_bimt`` package
---------------------------------------

The ``pyramid_bimt`` package is not intended to be used as a standalone pyramid
application, but as a part of a BIMT app.

So to develop the ``pyramid_bimt`` package, you first need to
:ref:`setting-up-a-local-development-environment` for one of the BIMT apps,
then use :term:`mr.developer` to checkout a working copy of ``pyramid_bimt``:

.. code-block:: bash

    # cd into an app's local development environment
    $ cd <APP>

    # now mark pyramid_bimt as a "development" egg: this will checkout the
    # source of pyramid_bimt into the ``src/pyramid-bimt`` folder and link to
    # it inside the ``bin/pserver`` script
    $ bin/develop checkout pyramid-bimt
    $ bin/buildout

.. note::

    Note that the package name is ``pyramid_bimt`` but the egg name is
    ``pyramid-bimt``!

If you now start the server, or run tests, Pyramid will pick up changes that
you made inside the ``src/pytamid-bimt`` folder.

.. code-block:: bash

    # Start the development instance of Pyramid, with the local copy of bimt
    # code that is in src/pyramid-bimt
    $ bin/pserve etc/development.ini --reload
    $ make tests

Before pushing your ``pyramid_bimt`` changes to GitHub you need to `cd` into
the ``src/pyramid-bimt`` folder and run all tests there. These tests are
isolated from the app's environment, as they need to run in arbitrary apps.

.. code-block:: bash

    $ cd src/pyramid-bimt
    $ make tests

.. _pinning_versions:

Pinning versions
----------------

All eggs that we use need their versions pinned to ensure repeatability of our
builds. Everytime you run ``bin/buildout`` you will see un-pinned egg versions
printed out (if any). You need to add those to ``buildout.d/versions.cfg``.

In case the egg in question is also used in production, you need to pin its
version in ``requirements.txt`` file that is used by :term:`Heroku` in
production. To make sure that we are pinning to exact the same versions in
``versions.cfg`` and ``requirements.txt`` run the following:

.. code-block:: bash

    # re-build your environment with only the basic set of eggs, without any
    # development tools
    $ echo -e "[buildout]\nextends = buildout.d/base.cfg" > buildout.cfg
    $ bin/buildout

    # re-run buildout with overwrite-requirements-file flag enabled
    $ bin/buildout buildout:overwrite-requirements-file=true

    # inspect changes and commit them
    $ git add -p etc/auto_requirements.txt

    # revert back to development buildout
    $ echo -e "[buildout]\nextends = buildout.d/development.cfg" > buildout.cfg
    $ bin/buildout

The ``pyramid_bimt`` package pins versions of its dependencies and publishes
this in a ``versions-<VERSION>.cfg`` file on our internal PyPI server, next
to the tarball of the package. Apps should use this `versions` file in their
own ``version.cfg`` and just append app specific pins.

Database migrations
-------------------

We use :term:`alembic` to automatically generate migration scripts and to
automatically run available upgrades. Before you start you need to read the
`alembic docs <http://alembic.readthedocs.org/en/latest/tutorial.html>`_ and
the `DB migration tutorial on Heroku
<https://devcenter.heroku.com/articles/upgrade-heroku-postgres-with-pgbackups>`_.

To prepare a new migration script you need to clone the production database,
so you have a temporary DB to work with. Follow these steps to prepare one:

.. code-block:: bash

    # create a snapshot of the production DB
    $ heroku pgbackups:capture --expire

    # add a new empty DB
    $ heroku addons:add heroku-postgresql:dev

    # restore snapshot to the new DB
    $ heroku pgbackups:restore NEW_HEROKU_DB_NAME

    # get the new DB connection string
    $ heroku pg:credentials NEW_HEROKU_DB_NAME

    # modify the sqlalchemy.url in development.ini with the new connection string

Now you are ready to prepare a migration script. Run the following to ask
Alembic to generate a migration script for you::

    $ bin/alembic -c etc/development.ini -n app:main revision --autogenerate -m "XXX: describe task"

Review it, remove commented stuff and test::

    $ bin/alembic -c etc/development.ini -n app:main upgrade head

Then also test the downgrade step::

    $ bin/alembic -c etc/development.ini -n app:main downgrade -1



.. note::

    Alembic is smart enough to auto-generate upgrade/downgrade code for adding
    and removing tables and columns. However, most of other migration tasks
    require that you manually write migration code.


Using a git checkout of pyramid_bimt on an app build on Travis
--------------------------------------------------------------

Use-case: you are developing a new feature inside a branch in an app. Your code
depends on latest (unreleased) changes in ``pyramid_bimt``. You need these
changes to run tests on Travis.

We have a read-only user ``bimt`` on GitHub. Use this user to clone
``pyramid_bimt`` inside an app's Travis build, like so:

#. [First time only] Add ``bimt`` user's password as an encrypted environment
   variable in Travis:

   .. code-block:: bash

       $ travis encrypt BIMT_GITHUB_PASSWORD=<SECRET> --add

#. Add the following snippet to ``buildout.d/travis.cfg``:

   .. code-block:: ini

       parts += environment
       extensions += mr.developer
       auto-checkout = pyramid-bimt

       [sources]
       pyramid-bimt = git https://bimt:${environment:BIMT_GITHUB_PASSWORD}@github.com/niteoweb/pyramid_bimt.git

       [environment]
       recipe = collective.recipe.environment

#. If you need code that is in a branch inside the ``pyramid_bimt`` repo, then
   append ``branch=yourbranch`` to the line in ``[sources]`` above.
