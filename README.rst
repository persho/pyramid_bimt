pyramid_bimt
============

A base project for BIMT apps. It provides:
 * SQLAlchemy ``Base`` & ``BaseMixin`` classes and thread local scoped
   ``Session`` (from the ``pyramid_basemodel`` package)
 * User model with email & password fields.
 * Login & Logout forms, authentication via passlib.
 * Number of events (user created, logged-in, etc.).
 * Extended request with ``request.user`` shortcut.

 Some parts are taken from the ``pyramid_simpleauth`` package.


 TODO
 ----

 * more granular permissions
 * /users view that admins can use to manage users
 * integration with JVZoo IPN