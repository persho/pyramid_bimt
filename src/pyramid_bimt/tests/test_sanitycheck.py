# -*- coding: utf-8 -*-
"""Testing sanity check view and email script."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt import register_utilities
from pyramid_bimt.testing import initTestingDB
from pyramid_mailer import get_mailer

import mock
import unittest


class TestCheckAdminUser(unittest.TestCase):

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_no_user_with_id_1(self, User):
        User.by_id.return_value = None

        from pyramid_bimt.sanitycheck import CheckAdminUser
        self.assertEqual(
            CheckAdminUser()(),
            ['User "admin" should have id of "1".'],
        )

    @mock.patch('pyramid_bimt.sanitycheck.User')
    @mock.patch('pyramid_bimt.sanitycheck.Group')
    def test_admin_not_disabled(self, Group, User):
        Group.by_name.return_value = 'admins'

        user = mock.Mock()
        user.enabled = True
        user.groups = ['admins', ]
        User.by_id.return_value = user

        from pyramid_bimt.sanitycheck import CheckAdminUser
        self.assertEqual(
            CheckAdminUser()(),
            ['User "admin" should be disabled in production.'],
        )

    @mock.patch('pyramid_bimt.sanitycheck.User')
    @mock.patch('pyramid_bimt.sanitycheck.Group')
    def test_admin_not_in_admins_group(self, Group, User):
        Group.by_name.return_value = 'admins'

        user = mock.Mock()
        user.enabled = False
        user.groups = ['users', ]
        User.by_id.return_value = user

        from pyramid_bimt.sanitycheck import CheckAdminUser
        self.assertEqual(
            CheckAdminUser()(),
            ['User "admin" should be in "admins" group.'],
        )

    @mock.patch('pyramid_bimt.sanitycheck.User')
    @mock.patch('pyramid_bimt.sanitycheck.Group')
    def test_no_warnings(self, Group, User):
        group = mock.Mock()
        Group.by_name.return_value = group

        user = mock.Mock()
        user.enabled = False
        user.groups = [group, ]
        User.by_id.return_value = user

        from pyramid_bimt.sanitycheck import CheckAdminUser
        self.assertEqual(
            CheckAdminUser()(),
            [],
        )


class TestCheckDefaultGroups(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanitycheck.Group')
    def test_default_groups_missing(self, Group):
        Group.by_name.return_value = None

        from pyramid_bimt.sanitycheck import CheckDefaultGroups
        self.assertEqual(
            CheckDefaultGroups()(),
            [
                'Group "admins" missing.',
                'Group "enabled" missing.',
                'Group "trial" missing.',
            ],
        )

    @mock.patch('pyramid_bimt.sanitycheck.Group')
    def test_no_warnings(self, Group):
        Group.by_name.return_value = True

        from pyramid_bimt.sanitycheck import CheckDefaultGroups
        self.assertEqual(
            CheckDefaultGroups()(),
            [],
        )


class TestCheckUsersProductGroup(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_no_product_group(self, User):
        from sqlalchemy.orm.exc import NoResultFound
        user = mock.Mock()
        p = mock.PropertyMock(side_effect=NoResultFound('Boom!'))
        type(user).product_group = p
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProductGroup
        self.assertEqual(CheckUsersProductGroup()(), [])

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_single_product_group(self, User):
        user = mock.Mock()
        user.product_group = 'foo'
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProductGroup
        self.assertEqual(CheckUsersProductGroup()(), [])

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_multiple_product_groups(self, User):
        from sqlalchemy.orm.exc import MultipleResultsFound
        user = mock.Mock()
        user.id = 1
        user.email = 'foo@bar.com'
        p = mock.PropertyMock(side_effect=MultipleResultsFound('Boom!'))
        type(user).product_group = p
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProductGroup
        self.assertEqual(
            CheckUsersProductGroup()(),
            ['User foo@bar.com (1) has multiple product groups.'],
        )


class TestCheckUsersProperties(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_fullname_is_None(self, User):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = None
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProperties
        self.assertEqual(
            CheckUsersProperties()(),
            ['User foo@bar.com (2) has an empty fullname.', ]
        )

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_fullname_is_empty_string(self, User):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = ''
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProperties
        self.assertEqual(
            CheckUsersProperties()(),
            ['User foo@bar.com (2) has an empty fullname.', ]
        )

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_fullname_is_spaces(self, User):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = '  '
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProperties
        self.assertEqual(
            CheckUsersProperties()(),
            ['User foo@bar.com (2) has an empty fullname.', ]
        )

    @mock.patch('pyramid_bimt.sanitycheck.User')
    def test_no_warnings(self, User):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = 'Foo'
        User.get_all.return_value = [user, ]

        from pyramid_bimt.sanitycheck import CheckUsersProperties
        self.assertEqual(
            CheckUsersProperties()(),
            [],
        )


class CheckUsersEnabledDisabled(unittest.TestCase):
    def setUp(self):
        from pyramid_bimt.tests.test_user_model import _make_user
        testing.setUp()
        initTestingDB(auditlog_types=True, groups=True)
        self.user = _make_user()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def _make_disabled_entry(self):
        from pyramid_bimt.models import AuditLogEventType
        from pyramid_bimt.tests.test_auditlog_model import _make_entry
        _make_entry(
            user=self.user,
            event_type=AuditLogEventType.by_name('UserDisabled'),
        )

    def _make_enabled_entry(self):
        from pyramid_bimt.models import AuditLogEventType
        from pyramid_bimt.tests.test_auditlog_model import _make_entry
        _make_entry(
            user=self.user,
            event_type=AuditLogEventType.by_name('UserEnabled'),
        )

    def test_enabled_correct(self):
        self.user.enable()
        self._make_enabled_entry()
        Session.flush()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            [],
        )

    def test_enabled_was_disabled_correct(self):
        self.user.enable()
        self._make_disabled_entry()
        self._make_enabled_entry()
        Session.flush()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            [],
        )

    def test_disabled_correct(self):
        self.user.disable()
        self._make_disabled_entry()
        Session.flush()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            [],
        )

    def test_disabled_was_enabled_correct(self):
        self.user.disable()
        self._make_enabled_entry()
        self._make_disabled_entry()
        Session.flush()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            [],
        )

    def test_enabled_no_entry(self):
        self.user.enable()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            ['User foo@bar.com (1) is enabled, but has no UserEnabled entry.'],
        )

    def test_enabled_disabled_entry_after_enabled(self):
        self.user.enable()
        self._make_disabled_entry()
        self._make_enabled_entry()
        self._make_disabled_entry()
        Session.flush()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            ['User foo@bar.com (1) is enabled, but has an UserDisabled entry'
                ' after UserEnabled entry.'],
        )

    def test_disabled_no_entry(self):
        self.user.disable()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            ['User foo@bar.com (1) is disabled, but has no UserDisabled entry.'],  # noqa
        )

    def test_disabled_enabled_entry_after_disabled(self):
        self.user.disable()
        self._make_enabled_entry()
        self._make_disabled_entry()
        self._make_enabled_entry()
        Session.flush()

        from pyramid_bimt.sanitycheck import CheckUsersEnabledDisabled
        self.assertEqual(
            CheckUsersEnabledDisabled()(),
            ['User foo@bar.com (1) is disabled, but has an UserEnabled entry'
                ' after UserDisabled entry.'],
        )


class TestRunAllChecks(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True, users=True)
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        register_utilities(self.config)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_warnings(self):
        check_admin_user = mock.Mock()
        check_default_groups = mock.Mock()
        check_users_properties = mock.Mock()

        check_admin_user.return_value.return_value = []
        check_default_groups.return_value.return_value = []
        check_users_properties.return_value.return_value = []

        def utilities(interface):
            return [
                check_admin_user, check_default_groups, check_users_properties
            ]

        self.request.registry.getAllUtilitiesRegisteredFor = utilities
        from pyramid_bimt.sanitycheck import run_all_checks
        self.assertEqual(run_all_checks(self.request), [])

    def test_one_warnings(self):
        from pyramid_bimt.models import AuditLogEntry
        check_admin_user = mock.Mock()
        check_default_groups = mock.Mock()
        check_users_properties = mock.Mock()

        check_admin_user.return_value.return_value = ['admin warning', ]
        check_default_groups.return_value.return_value = []
        check_users_properties.return_value.return_value = []

        def utilities(interface):
            return [
                check_admin_user, check_default_groups, check_users_properties
            ]

        self.request.registry.getAllUtilitiesRegisteredFor = utilities

        from pyramid_bimt.sanitycheck import run_all_checks
        self.assertEqual(
            run_all_checks(self.request),
            ['admin warning', ],
        )
        auditlog = AuditLogEntry.get_all(security=False).first()
        self.assertEqual(auditlog.user.id, 1)
        self.assertEqual(auditlog.comment, u'admin warning')

    def test_some_warnings(self):
        from pyramid_bimt.models import AuditLogEntry
        check_admin_user = mock.Mock()
        check_default_groups = mock.Mock()
        check_users_properties = mock.Mock()

        check_admin_user.return_value.return_value = ['admin warning', ]
        check_default_groups.return_value.return_value = ['groups warning', ]
        check_users_properties.return_value.return_value = ['user warning']

        def utilities(interface):
            return [
                check_admin_user, check_default_groups, check_users_properties
            ]

        self.request.registry.getAllUtilitiesRegisteredFor = utilities

        from pyramid_bimt.sanitycheck import run_all_checks
        self.assertEqual(
            run_all_checks(self.request),
            [
                'admin warning',
                'groups warning',
                'user warning',
            ],
        )
        auditlog = AuditLogEntry.get_all(security=False).first()
        self.assertEqual(auditlog.user.id, 1)
        self.assertEqual(
            auditlog.comment,
            u'admin warning, groups warning, user warning'
        )

    def test_one_warning(self):
        check_admin_user = mock.Mock()
        check_default_groups = mock.Mock()
        check_users_properties = mock.Mock()

        check_admin_user.return_value.return_value = ['admin warning', ]
        check_default_groups.return_value.return_value = ['groups warning', ]
        check_users_properties.return_value.return_value = ['user warning']

        def utilities(interface):
            return [
                check_admin_user, check_default_groups, check_users_properties
            ]

        self.request.registry.getAllUtilitiesRegisteredFor = utilities

        from pyramid_bimt.sanitycheck import run_all_checks
        self.assertEqual(
            run_all_checks(self.request),
            [
                'admin warning',
                'groups warning',
                'user warning',
            ],
        )


class TestSanityCheckView(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        self.request = testing.DummyRequest()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanitycheck.run_all_checks')
    @mock.patch('pyramid_bimt.sanitycheck.app_assets')
    def test_assets(self, app_assets, run_all_checks):
        run_all_checks.return_value = []

        from pyramid_bimt.sanitycheck import sanitycheck_view
        sanitycheck_view(self.request)
        app_assets.need.assert_called_with()

    @mock.patch('pyramid_bimt.sanitycheck.run_all_checks')
    def test_view_result(self, run_all_checks):
        run_all_checks.return_value = ['warning1', 'warning2']

        from pyramid_bimt.sanitycheck import sanitycheck_view
        result = sanitycheck_view(self.request)
        self.assertEqual(result, {'warnings': ['warning1', 'warning2']})


class TestSanityCheckEmail(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
            'mail.default_sender': 'info@bar.com'
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        self.config.include('pyramid_chameleon')
        self.request = testing.DummyRequest()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.scripts.sanitycheck_email.run_all_checks')
    def test_no_warnings(self, run_all_checks):
        run_all_checks.return_value = []

        from pyramid_bimt.scripts.sanitycheck_email import send_email
        send_email(self.config.registry.settings, self.request)

        mailer = get_mailer(self.config)
        self.assertEqual(len(mailer.outbox), 0)

    @mock.patch('pyramid_bimt.scripts.sanitycheck_email.run_all_checks')
    def test_some_warnings(self, run_all_checks):
        run_all_checks.return_value = ['warning1', 'warning2']

        from pyramid_bimt.scripts.sanitycheck_email import send_email
        send_email(self.config.registry.settings, self.request)

        mailer = get_mailer(self.config)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].recipients, ['maintenance@niteoweb.com', ])
        self.assertEqual(
            mailer.outbox[0].subject, u'BIMT sanity check found 2 warnings')

        self.assertIn(
            'The following warnings were found:', mailer.outbox[0].html)
        self.assertIn('<td>warning1</td>', mailer.outbox[0].html)
        self.assertIn('<td>warning2</td>', mailer.outbox[0].html)

    @mock.patch('pyramid_bimt.scripts.sanitycheck_email.run_all_checks')
    def test_no_warnings_verbose(self, run_all_checks):
        run_all_checks.return_value = []

        from pyramid_bimt.scripts.sanitycheck_email import send_email
        send_email(self.config.registry.settings, self.request, verbose=True)

        mailer = get_mailer(self.config)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].recipients, ['maintenance@niteoweb.com', ])
        self.assertEqual(
            mailer.outbox[0].subject, u'BIMT sanity check OK')
        self.assertIn(
            'Everything in order, nothing to report.', mailer.outbox[0].html)
