pyramid_bimt
============

A base project for BIMT apps. It provides:
 * SQLAlchemy ``Base`` & ``BaseMixin`` classes and thread local scoped
   ``Session`` (from the ``pyramid_basemodel`` package)
 * User model with email & password fields.
 * Login & Logout forms, authentication via passlib.
 * Number of events (user created, logged-in, etc.).
 * Extended request with ``request.user`` shortcut.

 Some parts are shamelessly stolen from the ``pyramid_simpleauth`` package.


 TODO
 ----

 * forgot password
 * integration with JVZoo IPN
 * join_date
 * history/audit log (changes, login, etc.)
