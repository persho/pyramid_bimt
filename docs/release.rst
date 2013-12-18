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

.. warning::

    At the time of writing, there is a bug on Travis, that prevents releases
    on git tags. So we currently do releases on Travis on every push to master
    branch. The process above needs to be paused after step 2 (so before
    giving the new development version to zest.releaser). Pause it by just not
    answering to zest.release, open up a new terminal and push changes to
    master. Wait a few minutes and Travis should have uploaded a new version
    from master to our PyPI. Once it is there, return to the initial terminal
    window and continue with zest.releaser process.
