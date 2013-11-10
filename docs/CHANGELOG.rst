:orphan:

Changelog
=========


0.1.4 (unreleased)
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
