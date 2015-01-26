Changelog
=========


0.32 (2015-01-26)
-----------------

- Add support for ignoring arbitrary IPN products, refs #1807.
  [zupo]


0.31.1 (2015-01-23)
-------------------

- Robot tests fix.
  [zupo]


0.31 (2015-01-23)
-----------------

- [MIGRATION REQUIRED] Logout view now expects POST request that contains
  ``csrf_token`` to prevent XSS logout. Apps need to correctly submit to that
  view where applicable (navbar).
  [ferewuz]

- Change all forms to correctly include and check CSRF token to prevent XSS
  attacks.
  [ferewuz]

- Allow disabled users access to Settings and Activity pages, refs #1785.
  [zupo]


0.30 (2015-01-20)
-----------------

- Load webfonts from CDN, refs #1622.
  [zupo]

- Don't allow site loading in iframes. Redirect when this happens.
  [ferewuz]


0.29 (2015-01-16)
-----------------

- [MIGRATION NEEDED] Add not found view. Forbidden view now redirects to not
  found. When on root it still redirects to login. Apps should now override
  404.pt template.
  [ferewuz]

- Allow Staff members to add and remove Auditlog Entries, refs #1756.
  [zupo]

- [MIGRATION NEEDED] Symmetric encryption can now be used where needed. User
  and group properties now have option to add them encrypted. API keys should
  be now encrypted and encryption used everywhere where applicable.
  [ferewuz]

- Settings UI changes to divide different parts of settings.
  [ferewuz]

- Add ``above_sidebar`` position option to portlets.
  [ferewuz]


0.28.1 (2015-01-11)
-------------------

- Robot fixes.
  [zupo]


0.28 (2015-01-11)
-----------------

- Added a new group ``impersonators`` whose members can use the ``login-as``
  view to impersonate other users.
  [zupo]

- Use default sender apps as a recipient for sanity check emails.
  [zupo]


0.27 (2014-12-19)
-----------------

- [MIGRATION NEEDED] Models should now use bimt mixins instead of implementing
  their own `by_id` and `by_name` methods.
  [ferewuz]


0.26 (2014-12-16)
-----------------

- [MIGRATION NEEDED] Correctly define UniqueConstraints.
  [zupo]


0.25 (2014-12-16)
-----------------

- Introduced the concept of a "product group" -- a group that has the
  ``product_id`` value set. A single user can only be a member of one such
  group.
  [zupo]

- Add user.id to body tag as data- attribute so it can be used in mixpanel JS.
  [zupo]


0.24 (2014-12-12)
-----------------

- Fix logging in scripts to correctly use app logging settings.
  [ferewuz]

- [MIGRATION REQUIRED] Sanity check now adds an audit log every time it is run.
  Apps need to add a SanityCheckDone audit log type to their DB.
  [ferewuz]

- Sanity check email script now has an option (--verbose) if you want the email
  to be sent on every check, or only on checks with warnings in them.
  [ferewuz]


0.23.2.1 (2014-12-04)
---------------------

- Fix robot tests that were broken in latest release.
  [ferewuz]


0.23.2 (2014-12-04)
-------------------

- Upgrade colander to version 1.0 to fix email validation error and get other
  improvements.
  [ferewuz]


0.23.1 (2014-12-02)
-------------------

- Only allow user enabling/disabling with views. Also add links for enabling
  and disabling to user view.
  [ferewuz]

- Add sanity checks for enabled/disabled users without proper audit entries.
  [ferewuz]

- Fix logout view when it is called while not being logged in.
  [ferewuz]


0.23 (2014-11-25)
-----------------

- [MIGRATION REQUIRED] Changes to Robot tests so they run faster:
    * do not load root page as part of suite setup -> this redirects and renders
      the login form, which is not cheap,
    * use RobotAPI to set appropriate cookies to simulate logging in, instead of
      actually going to the login form, filling it in and clicking Submit.

- Fix rendering of the Sanity Check view.
  [zupo]


0.22 (2014-11-20)
-----------------

- Upgrade Chosen plugin to support adding options to select field.
  [ferewuz]


0.21 (2014-11-18)
-----------------

- Upgrade to latest Font Awesome 4.2, to get the Google icon.
  [zupo]

- Correctly redirect to login page after reseting password.
  [ferewuz]


0.20 (2014-11-14)
-----------------

- Allow apps to provide their own sanity checks by registering ZCA Utilities
  that implement the ISanityCheck interface.
  [MIGRATION NEEDED] All apps need to update their Heroku Scheduler commands
  to run `sanitycheck_email` instead of `sanity_check_email`.
  [zupo]


0.19.2 (unreleased)
-------------------

- Fix 'name' and 'product_id' validators so existing groups can be edited.
  [zupo]


0.19.1.1 (2014-10-27)
---------------------

- Allow afilliate ID to be any string as jvzoo uses IDs instead of emails.
  [ferewuz]

- Added validator for billing email to prevent duplicates.
  [ferewuz]


0.19.1 (2014-10-20)
-------------------

- Added missing options for exclude_groups to portlet add and edit view.
  [ferewuz]


0.19 (2014-10-20)
-----------------
- [MIGRATION REQUIRED] Support for exclude groups on portlets similar to
  mailings, so admins can disable portlets for a selected group.
  [ferewuz]

- When adding groups if group with same name or product id already exist and
  return a validation error.
  [ferewuz]


0.18.5 (2014-10-16)
-------------------

- Fix datatables initialization to support more than one datatable on the
  same page.
  [ferewuz]


0.18.4.3 (2014-10-15)
---------------------

- Upgrade six to newest version.
  [ferewuz]


0.18.4.2 (2014-10-15)
---------------------

- Upgrade six to newest version.
  [ferewuz]


0.18.4.1 (2014-10-15)
---------------------

- Don't fail on unknown mode, it breaks robot tests on Travis.
  [zupo]


0.18.4 (2014-10-15)
-------------------

- Set ``settings['bimt.mode']`` mode-of-operation so apps can have code that
  runs only in development or production.
  [zupo]

- Fix AJAX datatable view problem as different instances of a view were using
  the same object for columns.
  [ferewuz]

- Fix bug when AuditLogEntry had the User connected to it deleted and still
  tried to get the user info.
  [ferewuz]

- Upon creating a user, immediately set the ``billing_email`` in case the user
  decides to change the login email, refs #830.
  [zupo]

- Handle the CANCEL-TEST-REBILL transaction type, refs #824.
  [zupo]


0.18.3.1 (2014-10-07)
---------------------

- More fixes for ClickBank IPN padding, refs #707.
  [zupo]


0.18.3 (2014-10-07)
-------------------

- Better filtering of zero-padded bytes from ClickBank, refs #707.
  [zupo]


0.18.2 (2014-10-05)
-------------------

- Remove default limits for get_all methods on all models.
  [ferewuz]

- Pinned repoze.sendmail to 4.1, because of a known bug in 4.2.
  [ferewuz]


0.18.1 (2014-10-01)
-------------------

- Fixes for undocumented ClickBank's padding.
  [zupo]


0.18 (2014-09-30)
-----------------

- [MIGRATION REQUIRED] Support for ClickBank Instant-Payment-Notifications. The
  ``group.product_id`` column needs to be converted from `Integer` to `String`.
  [zupo]


0.17.4 (2014-09-30)
-------------------

- BIMT should already include dependencies, so apps don't have to.
  [zupo]


0.17.3 (2014-09-30)
-------------------

- The `js.jquery-datatables` package was re-released, we can now use a public
  release instead of an internal one.
  [zupo]

- Alembic needs ``pyramid_mako``.
  [zupo]

- Change User get_all method to be case insensitive for fullname and email
  search.
  [ferewuz]

- Use jquery.datatables 1.10 to get state saving and other new features.
  [ferewuz]


0.17.2 (2014-09-26)
-------------------

- Refactor ``jvzoo.py`` into ``ipn.py`` so we can add support for additional
  marketplaces and not be limited to just JVZoo. However, currently only JVZoo
  is supported (with some placeholders already in place for ClickBank).
  [zupo]

- When behind a proxy, the ``request.cliend_addr`` will list multiple IPs. Only
  the first one is relevant for us.
  [zupo]


0.17.1 (2014-09-19)
-------------------

- Remove login successful notification.
  [ferewuz]

- Ajaxify users list to speed it up.
  [ferewuz]


0.17 (2014-09-15)
-----------------

- [MIGRATION REQUIRED] Apps should now use permissions from
  ``pyramid_bimt.const.BimtPermissions`` for views and explicit permission
  checking.
  [ferewuz]

- [MIGRATION REQUIRED] Apps should now use ``request.has_permission()`` instead
  of ``request.user.admin`` and similar.
  [ferewuz]

- [MIGRATION REQUIRED] When calling ``AuditLogEntry.get_all()`` with security
  enabled you have to pass it current request now.
  [ferewuz]

- [MIGRATION REQUIRED] Upgrade pyramid to 1.5.1. Apps need to set renderer
  explicitly in tests config where needed, like so:
  ``config.include('pyramid_chameleon')``.
  [ferewuz]

- [MIGRATION REQUIRED] Apps need to add the ``make versions`` command to their
  Makefile.
  [zupo]


0.16.1 (2014-09-08)
-------------------

- Fix robot api test problems.
  [ferewuz]


0.16 (2014-09-08)
-----------------

- Remove subscription button from settings when user is subscribed.
  [ferewuz]

- [MIGRATION REQUIRED] We now use layout.current_page for setting page title.
  All app's views should set page title by setting:
  ``self.request.layout_manager.layout.title`` with page title.
  [ferewuz]

- Nicer __repr__ for BIMT model classes.
  [zupo]

- Fixed bug with ACL which prevented admins to edit admins group.
  [ferewuz]

- [MIGRATION REQUIRED] Change routes to use paths with trailing slash. Fix unit
  and robot tests to comply with new changes.
  Apps need to:
  * Change app routes to contain trailing slash
  * Change the not found view config to
  ``@notfound_view_config(append_slash=True)``
  * Append ``/`` to the IPN URL inside JVZoo control panel
  [ferewuz]

- AuditLogEntry get_all method now works correctly. Limit was always overriding
  offset setting before which was problematic in AJAX datatable view.
  [ferewuz]


0.15.1 (2014-09-03)
-------------------

- Fix robot suite variables, so BROWSER environment variable gets used
  correctly.
  [ferewuz]

- More robust login_success, sometimes appstruct['password'] is not set.
  [zupo]

- The ``psycopg`` dependency needs to be an `install requirement` so it gets
  pushed into ``auto_requirements.txt`` in apps.
  [zupo]


0.15 (2014-08-24)
-----------------

- Fullnames containing only spaces now trigger a sanity check warning.
  [zupo]

- [MIGRATION REQUIRED] We now run robot tests with PhantomJS as they are about
  an order of magnitude faster than running against a full browser. Apps need
  to do the following migration tasks:
  * remove xvfb line from .travis.yml: ``export DISPLAY=:99.0; ...``
  * devs need to install PhantomJS on their local machines


0.14.3 (2014-08-20)
-------------------

- Avoid race conditions in auditlog robot tests.
  [zupo]

- Add Settings form to bimt so it can be used in apps to get rid of some DRY.
  [ferewuz]


0.14.2 (2014-08-15)
-------------------

- Fix JVZoo handling of re-curring BILL transactions. Refs #502.
  [zupo]

- AuditLogEntry.read should be a required field.
  [zupo]


0.14.1 (2014-08-15)
-------------------

- Fixed missing dependencies and version pins in 0.14 release.
  [zupo]


0.14 (2014-08-14)
-----------------

- [MIGRATION REQUIRED] More secure handling of sessions and cookies. Apps need
  to set the following values in their ini files:
  * session.type
  * session.key
  * session.secret
  * session.encrypt_key
  * session.validate_key
  * authtkt.secret
  The session.type should be 'cookie' in production.
  [zupo]

- Fix IP logging so it correctly logs client IP.
  [ferewuz]


0.13.2 (2014-08-03)
-------------------

- Fix a bug that prevented admins to edit users because email validation
  failed with "this email already exists" error.
  [zupo]


0.13.1 (2014-07-24)
-------------------

- Fix robot tests.
  [zupo]

- Use js.timeago on audit_log.pt.
  [zupo]


0.13 (2014-07-17)
-----------------

- Documentation on how to use travis-artifacts for uploading robot tests logs
  to S3 bucket on Travis build failure.
  [ferewuz]

- User IP, OS and browser gets logged on each login and saved as audit logs, so
  users (and admins) can check information for each login.
  [ferewuz]

- User view now includes a link to edit view.
  [ferewuz]

- Validator for changing email in settings that checks for duplicates. Should
  be used by all apps.
  [ferewuz]

- Additional validator when adding user, so we don't get any duplicates and
  therefore DB integrity errors.
  [ferewuz]

- [MIGRATION REQUIRED] Users can now see their Audit Log (which is named as
  Recent Activity in the UI).
  [zupo]


0.12 (2014-07-12)
-----------------

- [MIGRATION REQUIRED] Apps should now use/extend bimt's versions.cfg.
  [zupo]

- Staff members can now manage users & groups.
  [zupo]


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

- [DB MIGRATION REQUIRED] Add support for Celery tasks.
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
