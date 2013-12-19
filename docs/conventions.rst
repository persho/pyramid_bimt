Conventions & Assumptions
=========================

Code style guide
----------------

We follow `plone.api's style guide
<http://ploneapi.readthedocs.org/en/latest/contribute/conventions.html>`_. Read
it & use it.


Additional conventions
----------------------

#. When a change in ``pyramid_bimt`` requires database migration in an app,
   prefix the ``CHANGELOG.rst`` entry with ``[DB MIGRATION REQUIRED]``.
#. Each app provides its own `account` page, where users can modify their own
   info. This page is normally served on ``/settings``.
