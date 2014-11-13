# -*- coding: utf-8 -*-
"""Testing sanity check view and email script."""

from pyramid import testing
from pyramid_bimt import register_utilities
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


class TestRunAllChecks(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        register_utilities(self.config)

    def tearDown(self):
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
        self.assertEqual(run_all_checks(self.request.registry), [])

    def test_some_warnings(self):
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
            run_all_checks(self.request.registry),
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
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].recipients, ['maintenance@niteoweb.com', ])
        self.assertEqual(
            mailer.outbox[0].subject, u'BIMT sanity check OK')
        self.assertIn(
            'Everything in order, nothing to report.', mailer.outbox[0].html)

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
