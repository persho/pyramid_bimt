============
pyramid_bimt
============

Base package for BIMT Pyramid apps.

* `Source code @ GitHub <https://github.com/niteoweb/pyramid_bimt>`_
* `Documentation @ docs.niteoweb.com <http://docs.niteoweb.com/pyramid_bimt/>`_
* `Continuous Integration @ Travis CI <https://magnum.travis-ci.com/niteoweb/pyramid_bimt/builds/>`_

.. raw:: html

    <img src="https://magnum.travis-ci.com/niteoweb/pyramid_bimt.png?token=EfqGo6ntpjJ6E4arsYTQ&branch=master">
    <img src="https://s3.amazonaws.com/assets.coveralls.io/badges/coveralls_100.png">


Summary
=======

The ``pyramid_bimt`` package provides a common framework for `Big IM Toolbox
<http://www.bigimtoolbox.com>`_ apps to build upon. The package contains code
that is not specific to a certain app, but shared among many apps, such as:

* SQLAlchemy ``Base`` & ``BaseMixin`` classes and a thread local scoped
  ``Session`` (from the ``pyramid_basemodel`` package).
* User model with email, password and other common fields.
* Login, Logout, Password Reset forms, authentication via
  :ref:`passlib <passlib:context-overview>`.
* A number of events (user created, logged-in, etc.) that apps can
  subscribe to.
* Extended request with ``request.user`` shortcut.
* User management views for admins.
* Audit log for admins. Can be extended with per-app custom events.
* Simple portlets.
* Default layout using ``pyramid_layout``.
* Static resources handled by :ref:`Fanstatic <fanstatic:packaged_libs>`.
* Glyphicons and FontAwesome icon sets.
* Various UI JavaScript helpers.

This documentation describers best-practices on how to write and manage BIMT
apps.

