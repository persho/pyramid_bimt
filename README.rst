============
pyramid_bimt
============

A base project for BIMT apps. It provides:

* SQLAlchemy ``Base`` & ``BaseMixin`` classes and thread local scoped
  ``Session`` (from the ``pyramid_basemodel`` package)
* User model with email & password fields.
* Login & Logout forms, authentication via passlib.
* A number of events (user created, logged-in, etc.).
* Extended request with ``request.user`` shortcut.
* User management views for admins.

Some parts are shamelessly stolen from the ``pyramid_simpleauth`` package.


TODO
====

* forgot password form & email
* integration with JVZoo IPN
* join_date
* history/audit log (changes, login, etc.)
