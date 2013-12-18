============
pyramid_bimt
============

A base package for BIMT apps.

A Heroku-deployable Pyramid app for batch enriching text articles with images
and videos.

* `Source code @ GitHub <https://github.com/niteoweb/pyramid_bimt>`_
* `Dev Docs @ GitHub <https://github.com/niteoweb/pyramid_bimt/blob/master/docs/develop.rst>`_
* `Continuous Integration @ Travis-CI <https://magnum.travis-ci.com/niteoweb/pyramid_bimt/builds/>`_

.. raw:: html

    <img src="https://magnum.travis-ci.com/niteoweb/pyramid_bimt.png?token=EfqGo6ntpjJ6E4arsYTQ&branch=master">
    <img src="https://s3.amazonaws.com/assets.coveralls.io/badges/coveralls_100.png">


It provides a common base to develop BIMT projects/app from. Features:

* SQLAlchemy ``Base`` & ``BaseMixin`` classes and a thread local scoped
  ``Session`` (from the ``pyramid_basemodel`` package)
* User model with email & password fields.
* Login & Logout forms, authentication via passlib.
* A number of events (user created, logged-in, etc.).
* Extended request with ``request.user`` shortcut.
* User management views for admins.
* Audit log for admins. Can be extended with per-app custom events.



TODO
====

* better test coverage
