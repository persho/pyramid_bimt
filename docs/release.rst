Release process
===============

Releasing apps
--------------

BIMT apps do not need to be released as eggs. They are continuously deployed
to Heroku, on every push to master on GitHub.


Releasing ``pyramid_bimt``
--------------------------

Releases of ``pytamid_bimt`` are hosted on our private PyPI at
https://pypi.niteoweb.com. New releases are made automatically by
:term:`Travis` whenever a new tag is pushed to GitHub. To make a new release,
run ``make release``. This command will do the following:

#. Ask you for a version number for this release, update ``setup.py``/
   ``CHANGELOG.rst`` with it and offer to commit the version change.
#. Create a git tag with the name ``v{$VERSION}``.
#. Ask you for a version number for the next release and append ``.dev0`` to it
   to indicate it's in development. It will again update ``setup.py``/
   ``CHANGELOG.rst`` and offer to commit changes.
#. Offer to push both commits and the new tag.
#. :term:`Travis` will then build the tag and deploy the new release to our
   internal PyPI so BIMT apps can start using it.

To use releases from our private PyPI in BIMT apps, you need to add the
following to app's buildout:

.. code-block:: ini

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

To use it in pip's ``requirements.txt`` file, add the following to the top
of it:

.. code-block:: bash

    -i https://niteoweb:ni6kixe2why9ga@pypi.niteoweb.com/simple


.. note::

    Follow `Semantic Versioning <http://semver.org>`_ to decide what the next
    version number should be.

.. note::

    If release requires database migration in an app, bump the major version
    number.


Internal releases of third-party libs
-------------------------------------

Sometimes we need to do internal releases of third-party libraries. The most
common use case is when you need some fixes that are available in an unreleased
version of the upstream package. The second use case is when you need to have
custom patches in a third-party lib, that cannot be pushed upstream.

To fork it or not to fork it
""""""""""""""""""""""""""""

If you need custom patches in a third-party lib, fork it to the ``niteoweb``
GitHub account, apply your patches (remember to update the `Changelog`) and
push them to your fork.

In case you only need fixes available in an unreleased version of the package
there is no need for forking.

.. _third_party_version_number:

Version number
""""""""""""""

Use the same version that is currently in setup.py, but append the SHA1
revision number of the latest commit that you will include in the release.

For example, if a third-party package has version `1.2.3` in its setup.py file
and is currently at revision `0663830d9b18309784ff390531f8291764744386` the new
version number would become::

    1.2.3-0663830d9b18309784ff390531f8291764744386

Creating a release
""""""""""""""""""

Creating a new release of a package consists of the following steps:

#. Select a new :ref:`version number <third_party_version_number>` and apply
   it to ``setup.py``.
#. Update ``CHANGELOG.rst`` if you applied any patches.
#. Release and upload to ``pypi.niteoweb.com``:

   .. code-block:: bash


        $ mkrelease --no-commit --no-tag -d pypi.niteoweb.com src/third.party

.. note::
    You need to have ``jarn.mkrelease`` installed in order to run the
    ``mkrelease`` command.

.. note::
    Do not commit changes to setup.py. You are making an internal release of
    a third-party library, and you will not push your changes to setup.py to
    the public.

.. note::

    Your ~/.pypirc needs to contain the following to be able to upload eggs
    to our internal PyPI server:

    .. code-block:: ini

        [pypi.niteoweb.com]
        repository = https://pypi.niteoweb.com
        username = niteoweb
        password = ni6kixe2why9ga
