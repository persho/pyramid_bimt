Changelog
=========


0.11.5 (unreleased)
-------------------

- Nothing changed yet.


0.11.4 (2014-07-09)
-------------------

- CloudAMQP connections killing now optional. Apps need to set
  'bimt.kill_cloudamqp_connections' to False to not kill connections on
  startup.
  [ferewuz]


0.11.3 (2014-06-21)
-------------------

- Add support for assigning CSS classes to rows in AJAX generated DataTables
  tables.
  [zupo]


0.11.2 (2014-06-20)
-------------------

- Add option for additional filtering in datatables ajax views. When
  'filter_by.name' and 'filter_by_value' are in GET request, ajax view will
  filter results by that field.
  [ferewuz]


0.11.1 (2014-06-19)
-------------------

- Two new TaskStates: rerun and terminated.
  [zupo]

- Load javascript plugins also after AJAX calls to get confirmation, timeago,
  and other funcionalities in datatables.
  [ferewuz]

- UserCreated event now fired on manual user creation and not only when Jvzoo
  creates new User.
  [ferewuz]


0.11 (2014-06-16)
-----------------

- A single TaskModel instance can now be reused by multiple celery tasks.
  Common use-case is rerunning failed tasks.
  [zupo]

- Present a nice error message to user when task fails.
  [zupo]

- Render HTML in bootstrap tooltips.
  [zupo]

- [DB MIGRATION REQUIRED] App's TaskModel needs new columns: traceback,
  args and kwargs.
  [zupo]

- [DB MIGRATION REQUIRED] Add GroupProperty that can be used by apps similar
  to UserProperty, to save additional data.
  [ferewuz]

- [DB MIGRATION REQUIRED] Add task.traceback field. Apps need to add the
  traceback column to their Task objects.
  [zupo]


0.10.3 (2014-06-11)
-------------------

- Robot bugfixes that came with adding Chosen jquery.
  [ferewuz]


0.10.2 (2014-06-10)
-------------------

- Chosen Jquery plugin added, so it makes all selects nicer and searchable.
  [ferewuz]

- Fixed encoding errors with task.on_failure().
  [zupo]

- UniqueConstraint names must be unique.
  [zupo]


0.10.1 (2014-06-04)
-------------------

- Robot DB initialization method now explicitly enables full demo content.
  [ferewuz]


0.10 (2014-05-29)
-----------------

- Change robot suite startup so it initalizes DB by itself and can use same
  server for multiple tests. Apps need to change test startup, so it uses just
  one server and set app name as env variable.
  [ferewuz]

- Add cache on travis builds, so that builds run much faster as they do not
  need to fetch all dependencies each time.
  [ferewuz]


0.9.1 (2014-05-28)
------------------

- Testing Travis' deploy-on-tag.
  [zupo]


0.9 (2014-05-28)
----------------

- [DB MIGRATION REQUIRED] Add login as view that allows admins and staff to
  login as every other user. Staff group needs to be added to apps.
  [ferewuz]

- Set 'admin' as default view permission to prevent accidental leaks.
  Apps need to change view permission. Where default permission was being used,
  now they should use: pyramid.security.NO_PERMISSION_REQUIRED.
  [ferewuz]

- Flash messages can now contain HTML elements.
  [zupo]

- [DB MIGRAITON REQUIRED] Add support for Celery tasks.
  [zupo]

- Display an "Insufficient privileges" flash message when redirecting to
  login form because of denied access.
  [zupo]

- Remove the ``personal`` permission as it's only used in settings view, and
  this view can easily use the ``user`` permission.
  [zupo]

- Login-form should not display any sidebars.
  [zupo]

- [DB MIGRATION REQUIRED] Add forward_ipn_url field to groups, so we can
  re-send jvzoo IPN request to other apps and chain it if we want to.
  [ferewuz]

- Refactor of jvzoo view as complexity was over the limit.
  [ferewuz]

- Support for overriding sorting settings on datatables with query string
  URL parameters.
  [zupo]

- Support for fuzzy timestamps with jquery.timeago.js.
  [zupo]


0.8.3 (2014-05-19)
------------------

- Fixed a bug where a password reset would send out two Mailings: welcome
  mailing and password reset mailing. Only the latter should be sent.
  [zupo]


0.8.2 (2014-05-19)
------------------

- Brown-bag release.
  [zupo]


0.8.1 (2014-05-16)
------------------

- Minor fixes from deploying 0.8.
  [zupo]


0.8 (2014-05-15)
----------------

- Refactor robot tests so none of them depend on each other. All of
  them expect clean DB. Apps have to change robot suite initialization to
  always use clean DB.
  [ferewuz]

- [DB MIGRAITON REQUIRED] Remove hard-coded emails (welcome, password reset,
  etc.) and make them Mailings, refs #186.
  [ferewuz]

- [DB MIGRAITON REQUIRED] Add event triggers for Mailings (after password
  change, after user created, etc.), refs #320.
  [ferewuz]

- Add support for AJAX loading of data into jQuery.dataTables, refs #358.
  [ferewuz, zupo]

- Auto-kill rabbitmq connections on app start.
  [matejc]

- Split models.py into several sub-modules.
  [matejc]

- Portlets changed, they are now rendered using a template. Fixes #355.
  [ferewuz]


0.7.2 (2014-04-24)
------------------

- UniqueConstraint names must be unique.
  [zupo]


0.7.1 (2014-04-24)
------------------

- [DB MIGRAITON REQUIRED] Support for unsubscribing from Mailings.
  [matejc]


0.7 (2014-04-20)
----------------

- [DB MIGRATION REQUIRED] Add ``.../unsubscribe`` view and ``Exclude Groups``
  to Mailing page. When upgrading to this version, upgrade step must be run
  on applications to add 'exclude_mailing_group' relation table
  and add group ``unsubscribed``.
  [matejc]


0.6.3.1 (2014-04-18)
--------------------

- Brown-bag release.
  [zupo]


0.6.3 (2014-04-18)
------------------

- Fix for #341.
  [zupo]

- Adjusted @@sanity-check to make sure admin user is disabled in production.
  [zupo]

- Documentation on how to enable IRC notifications from GetSentry.
  [zupo]


0.6.2.1 (2014-04-08)
--------------------

- Bugfix for 0.6.2.
  [zupo]


0.6.2 (2014-04-08)
------------------

- Support for ColanderAlchemy 0.3.1.
  [zupo]


0.6.1 (2014-03-21)
------------------

- Support for form descriptions.
  [matejc]


0.6 (2014-03-13)
----------------

- Email API key with credentials to new user (created by jvzoo).
  [matejc]

- Fix scheduled scripts: they did not run and did not send out emails.
  [zupo]

- Provide and document using a standard template for emails.
  [zupo]

- Ship ``bootbox.js`` with this package so we can have simple confirmation
  modals for form submissions.
  [zupo]

- Hide confidential information on ``/config`` with the `secret span` approach.
  [zupo]

- Hard-coded payment reminders removed in favor of TTW mailings. Apps can now
  remove what they needed to add in 0.4.6.
  [zupo]

- Support creation of scheduled mailings via the web UI.
  [zupo]


0.5.3 (2014-03-08)
------------------

- Fix setting user's password through User Edit form. Refs #299.
  [zupo]


0.5.2 (2014-02-27)
------------------

- When editing a User with an existing UserProperty, do not re-create the
  UserProperty, but update the existing one. Fixes #277.
  [zupo]


0.5.1 (2014-02-14)
------------------

- FontAwesome icons are now bundled with this package.
  [zupo]

- Tooltips can now be displayed on any DOM element, not just spans.
  [zupo]


0.5 (2014-02-07)
----------------

- [DB MIGRATION REQUIRED] Support per-group definition of validity period and
  trial/regular. The ``bimt.jvzoo_regular_period`` and
  ``bimt.jvzoo_regular_period`` settings are now obsolete and should be removed
  from ``*.ini`` files.
  [zupo]

- The route naming policy was updated to be more consistent and clean.
  [zupo]

- [DB MIGRATION REQUIRED] Sanity check view added that checks if all users are
  correctly divided into groups and sends mail on selected address with
  results. View can be used by admins or script called externally.
  [ferewuz]

- [DB MIGRATION REQUIRED] Groups overhaul. 'users' group changed to 'enabled',
  'trial' and 'regular' groups added, jvzoo logic changed to divide users in
  different groups.
  [ferewuz]

- [DB MIGRATION REQUIRED] Last payment field added to users table, which will
  help us with payment reminders.
  [ferewuz]

0.4.6 (2014-01-08)
------------------

- Payment reminders feature. Apps need to:
  * Set ``bimt.pricing_page_url`` to pricing page to be send along with some emails.
  * Set ``bimt.payment_reminders``, currently there are 4 templates: ``first``, ``second``, ``third`` and final ``fourth``. Example: ``{"first": {"months": 1, "days": 3}, "second": {"months": 0, "days": 17}}``
  * Add a daily scheduled task to run the ``reminder_emails`` script.

- Allow forms based on FormView to hide the sidebar.
  [zupo]

- Add JS support for showing passwords on a click.
  [zupo]

- Fix to robot test resources
  [ferewuz]


0.4.5 (2014-01-02)
------------------

- Better support for ColanderAlchemy schemas in FormView.
  [zupo]

- Fix login URL in password reset email.
  [zupo]


0.4.4 (2013-12-31)
------------------

- Provide a base ``FormView`` class that apps can reuse to build form views.
  [zupo]

- Support for masked input fields.
  [zupo]

- Added valid_to field to user edit and add forms.
  [ferewuz]


0.4.3 (2013-12-23)
------------------

- Provide ${APP_NAME}, ${APP_TITLE} and ${APP_DOMAIN} global variables in robot
  tests we can have better tests.
  [zupo]


0.4.2 (2013-12-23)
------------------

- Fix for emails path in robot tests.
  [zupo]


0.4.1 (2013-12-22)
------------------

- This package now provides base resources for robot-framework tests in apps,
  along with robot-framework tests for login/logout/password-reset.
  [zupo]


0.4 (2013-12-20)
----------------

- Added lots of documentation. Read it!.
  [zupo]

- Sphinx docs are now auto-uploaded to docs.niteoweb.com on every successful
  Travis build.
  [zupo]

- [DB MIGRATION REQUIRED] Add the Portlets feature, available on ``/portlets``.
  [matejc]

- Util methods that are used in multiple applications added
  [ferewuz]

- Test coverage now at 100%, all the missing tests were added.
  [ferewuz]

- Support for nice searchable/sortable tables with jQuery.DataTables.
  [zupo]

- Add tests for views that didn't have them, tests for AuditLogEvent,
  small fix to user edit form.
  [ferewuz]

- [DB MIGRATION REQUIRED] We always store emails in lower-case.
  [zupo]


0.3.2 (2013-12-13)
------------------

- Libraries (such as pyramid_bimt) need to include compiled resources.
  [zupo]


0.3.1 (2013-12-13)
------------------

- Redirect user to value of settings entry named
  'bimt.disabled_user_redirect_path'. The value is path, ex: /settings
  [matejc]

- Added a non-admin user to 'add_default_content' for testing env.
  [matejc]

- Move flash messages back to the content area.
  [zupo]

- Various fixes for Fanstatic integration.
  [zupo]


0.3 (2013-12-12)
----------------

- Handle all static resources with Fanstatic. Overhaul of templates and
  CSS/JS files.
  [zupo]

- Redirect to user view after edit user.
  [matejc]

- Expired_subscriptions script now writes an AuditLog entry when disabling a
  user.
  [zupo]

- Allow views to hide the sidebar by setting the
  ``request.layout_manager.layout.hide_sidebar`` value to ``True``.
  [zupo]

- Fix for exceptions in verify password function, returns False on Exception.
  [matejc]


0.2.3 (2013-12-06)
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
