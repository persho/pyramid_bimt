============
pyramid_bimt
============

A base package for BIMT apps. It provides:

* SQLAlchemy ``Base`` & ``BaseMixin`` classes and a thread local scoped
  ``Session`` (from the ``pyramid_basemodel`` package)
* User model with email & password fields.
* Login & Logout forms, authentication via passlib.
* A number of events (user created, logged-in, etc.).
* Extended request with ``request.user`` shortcut.
* User management views for admins.
* Audit log for admins. Can be extended with per-app custom events.

Some parts are shamelessly stolen from the ``pyramid_simpleauth`` package.


TODO
====

* forgot password form & email
* integration with JVZoo IPN
* user enable/disable
