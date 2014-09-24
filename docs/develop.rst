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

If you now start the server, or run tests, Pyramid will pick up any changes
that you make inside the ``src/pyramid-bimt`` folder.

.. code-block:: bash

    # Start the development instance of Pyramid, with the local copy of
    # pyramid_bimt code that is in src/pyramid-bimt
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

    $ make versions

This command will make appropriate changes in ``requirements.txt`` file and
add them to your git staging area, ready for you to commit them.

The ``pyramid_bimt`` package pins versions of its dependencies and publishes
them in a ``versions-<VERSION>.cfg`` file on our internal PyPI server, next
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

Running robot-framework tests locally
-------------------------------------

Robot tests are system tests that verify functionality from the top-most level:
from the browser. They simulate clicking and entering data, validating
resulting HTML. JavaScript is run before HTML is validated so our JS files
are also tested this way. For performance purposes, by default, robot tests run
against a headless browser implementation called `PhantomJS`.

  .. code-block:: ini

    # install PhantomJS
    $ {apt-get/brew/yum} install npm
    $ npm install -g phantomjs

    # run robot tests
    $ make robot


To run robot tests against an actual browser for easier development and
debugging, set the BROWSER environment variable:

  .. code-block:: ini

    $ BROWSER=Firefox make robot


Uploading robot-framework logs on Amazon S3
-------------------------------------------

When you are running robot tests on Travis you cannot see logs and screenshots
of robot tests. To help with identifying the problems you can set up your app
so that every time the robot tests are failing, it uploads the logs to Amazon
S3 bucket.

You should prepare a S3 bucket and make IAM user with the following
policy active on your IAM user:

.. code-block:: xml

    {
      "Statement": [
        {
          "Action": [
            "s3:GetBucketLocation",
            "s3:ListAllMyBuckets"
          ],
          "Effect": "Allow",
          "Resource": [
            "arn:aws:s3:::*"
          ]
        },
        {
          "Action": [
            "s3:*"
          ],
          "Effect": "Allow",
          "Resource": [
            "arn:aws:s3:::<your-bucket-name>"
          ]
        },
        {
          "Action": [
            "s3:*"
          ],
          "Effect": "Allow",
          "Resource": [
            "arn:aws:s3:::<your-bucket-name>/*"
          ]
        }
      ]
    }

In ``.travis.yml`` you have to set 4 environment variables:

.. code-block:: yaml

    - ARTIFACTS_AWS_REGION=<Region of your S3 bucket>
    - ARTIFACTS_S3_BUCKET=<Name of your S3 bucket>

You should also add your IAM user's ``ARTIFACTS_AWS_ACCESS_KEY_ID`` and
``ARTIFACTS_AWS_SECRET_ACCESS_KEY``, but you should add both encrypted.

.. code-block:: bash

    $ travis encrypt ARTIFACTS_AWS_ACCESS_KEY_ID=<iam_user_access_key> --add
    $ travis encrypt ARTIFACTS_AWS_SECRET_ACCESS_KEY=<iam_user_secret_key> --add

Add travis-artifacts to your travis install step (preferrably with bundler as done `here <https://github.com/niteoweb/ebn/commit/9fbf24b245808dcf2bbc7142cf8c19023f174c04>`_.)
and add travis-artifacts step to your ``after_failure`` step.

.. code-block:: yaml

    after_failure: # Upload robot tests screenshots on failure
      - "travis-artifacts upload --path parts/robot/ --target-path <app_name>/$TRAVIS_BUILD_NUMBER"


Now on every build that fails Travis will upload robot logs to your S3
bucket, each build into different folder. You can access your robot logs
through `Amazon console <https://niteoweb.signin.aws.amazon.com/console>`_.


Mocking an Instant-Payment-Nofication from JVZoo and ClickBank
--------------------------------------------------------------

Whenever a new user makes a purchase we receive an :term:`IPN` POST request
from payment providers servers to our servers. We parse the POST and create a
new user account.

To mock this POST request from JVZoo, use the following command:

.. code-block:: bash

    $ curl -d "ccustname=JohnSmith&ccuststate=&ccustcc=&ccustemail=jvzoo@bar.com&cproditem=1&cprodtitle=TestProduct&cprodtype=STANDARD&ctransaction=SALE&ctransaffiliate=aff@bar.com&ctransamount=1234&ctranspaymentmethod=&ctransvendor=&ctransreceipt=1&cupsellreceipt=&caffitid=&cvendthru=&cverify=D1EA7E5A&ctranstime=1350388651" http://localhost:8080/jvzoo/

To mock this POST request from JVZoo, use the following command:

.. code-block:: bash

    $ curl -d "TODO" http://localhost:8080/clickbank/


The commands above assumes you have set your ``bimt.jvzoo_secret_key`` and
``bimt.clickbank_secret_key``, respectively, set to ``secret`` in your local
app (this is the default value).
