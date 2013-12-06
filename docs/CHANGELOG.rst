:orphan:

Changelog
=========


0.2.3 (unreleased)
------------------

- Overhaul of setting entries check, split them as default and production.
  [matejc]

- Config view at route /config where there is read only information about
  Pyramid setttings and environment variables.
  [matejc]

- Minor tweaks to welcome email.
  [zupo]

- Print to logger.info() on milestones in the JVZoo POST handling process.
  [zupo]


0.2.2 (2013-12-05)
------------------

- Additional fixes & tests for JVZoo integration.
  [zupo]

- Send more data to sentry using logger.exception().
  [zupo]


0.2.1 (2013-12-05)
------------------

- The jvzoo view was missing a renderer.
  [zupo]

- Fix "hash could not be identified" error.
  [zupo]


0.2 (2013-12-04)
----------------

- Integration with JVZoo Instant Payment Notification service. Apps need to:
  * Perform DB migration.
  * Set ``bimt.jvzoo_trial_period``, ``bimt.jvzoo_regular_period`` and
  ``bimt.jvzoo_secret_key`` settings.
  * Add a daily scheduled task to run the ``expire_subscriptions`` script.

- Rename ``IUserSignedUp`` to ``IUserCreated`` since users are created by the
  system, they do no sign up on themselves.
  [zupo]

- Remove ``IUserDeleted`` event, since we do not yet support deleting users.
  [zupo]

- Rewrite get methods in models classes to all be named in a consistent way:
  by_id(), by_email(), etc.
  [zupo]


0.1.9.1 (2013-12-03)
--------------------

- Fix raise-error/js.
  [zupo]


0.1.9 (2013-12-03)
------------------

- Support for integration with GetSentry. Apps need to provide the following:
   * include pyramid_raven in production.ini
   * configure sentry logger in production.ini
   * pass over SENTRY_DNS in Procfile



0.1.8 (2013-12-02)
------------------

- Moved ``/audit_log`` URL to ``/audit-log``.
  [zupo]

- Split ``views.py`` into ``views/`` sub-package.
  [zupo]

- Required options are ``mail.default_sender``, ``bimt.app_name``,
  ``bimt.app_title`` or application will fail at start. For example look
  at the ``development.ini``.
  [matejc]

- Add and edit user form, for now only email, full name and groups. All
  features are located in ``\users`` path. View/edit user options are in
  Options column for each member.
  [matejc]



0.1.7 (2013-11-27)
------------------

- Add fullname to /users and /user view.
  [matejc]

- Add bimt.piwik_site_id to default_layout.pt, trigger it by
  setting for example: `bimt.piwik_site_id = 102` to .ini file.
  [matejc]


0.1.6 (2013-11-10)
------------------

- Set correct unique constraint for ``key`` in ``UserProperty``.
  [zupo]

- More fixes to reset password email template.
  [zupo]


0.1.5 (2013-11-10)
------------------

- Fix reset password email template.
  [zupo]


0.1.4 (2013-11-10)
------------------

- Ignore ``tests/`` subpackage when doing Venusian scan.
  [zupo]


0.1.3 (2013-11-10)
------------------

- Added missing files to git.
  [zupo]


0.1.2 (2013-11-10)
------------------

- Added redirect from /users/ to /users.
  [zupo]

- Fixed regressions when refactoring UserSettings -> UserProperty.
  [zupo]


0.1.1 (2013-11-10)
------------------

- Added the 'default return value' feature to get_property().
  [zupo]

- Refactored UserSettings -> UserProperty.
  [zupo]

- Added generate() method for generating random strings to ``security.py`` so
  apps can reuse it.
  [zupo]

- Enabled developers to work on pyramid_bimt individually and not
  necessarily inside the scope of some other app.
  [zupo]

- Made ``pyramid_bimt`` provide default ``pyramid_layout`` layout. Apps can
  then use this default one or roll their own.
  [zupo]

- Added a basic password reset feature.
  [zupo]


0.1 (2013-11-08)
----------------

- Initial release.
  [offline, zupo]
