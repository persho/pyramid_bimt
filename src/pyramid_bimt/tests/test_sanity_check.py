# -*- coding: utf-8 -*-
"""Testing sanity check view and email script."""

from pyramid import testing
from pyramid_mailer import get_mailer

import mock
import unittest


class TestCheckAdmin(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanity_check.User')
    def test_no_user_with_id_1(self, User):
        User.by_id.return_value = None

        from pyramid_bimt.sanity_check import check_admin_user
        self.assertEqual(
            check_admin_user(),
            ['User "admin" should have id of "1".'],
        )

    @mock.patch('pyramid_bimt.sanity_check.User')
    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_admin_not_disabled(self, Group, User):
        Group.by_name.return_value = 'admins'

        user = mock.Mock()
        user.enabled = True
        user.groups = ['admins', ]
        User.by_id.return_value = user

        from pyramid_bimt.sanity_check import check_admin_user
        self.assertEqual(
            check_admin_user(),
            ['User "admin" should be disabled in production.'],
        )

    @mock.patch('pyramid_bimt.sanity_check.User')
    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_admin_not_in_admins_group(self, Group, User):
        Group.by_name.return_value = 'admins'

        user = mock.Mock()
        user.enabled = False
        user.groups = ['users', ]
        User.by_id.return_value = user

        from pyramid_bimt.sanity_check import check_admin_user
        self.assertEqual(
            check_admin_user(),
            ['User "admin" should be in "admins" group.'],
        )

    @mock.patch('pyramid_bimt.sanity_check.User')
    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_no_warnings(self, Group, User):
        group = mock.Mock()
        Group.by_name.return_value = group

        user = mock.Mock()
        user.enabled = False
        user.groups = [group, ]
        User.by_id.return_value = user

        from pyramid_bimt.sanity_check import check_admin_user
        self.assertEqual(
            check_admin_user(),
            [],
        )


class TestCheckDefaultGroups(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_default_groups_missing(self, Group):
        Group.by_name.return_value = None

        from pyramid_bimt.sanity_check import check_default_groups
        self.assertEqual(
            check_default_groups(),
            [
                'Group "admins" missing.',
                'Group "enabled" missing.',
                'Group "trial" missing.',
            ],
        )

    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_no_warnings(self, Group):
        Group.by_name.return_value = True

        from pyramid_bimt.sanity_check import check_default_groups
        self.assertEqual(
            check_default_groups(),
            [],
        )


class TestCheckUser(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_fullname_is_None(self, Group):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = None

        from pyramid_bimt.sanity_check import check_user
        self.assertEqual(
            check_user(user),
            ['User foo@bar.com (2) has an empty fullname.', ]
        )

    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_fullname_is_empty_string(self, Group):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = ''

        from pyramid_bimt.sanity_check import check_user
        self.assertEqual(
            check_user(user),
            ['User foo@bar.com (2) has an empty fullname.', ]
        )

    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_fullname_is_spaces(self, Group):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = '  '

        from pyramid_bimt.sanity_check import check_user
        self.assertEqual(
            check_user(user),
            ['User foo@bar.com (2) has an empty fullname.', ]
        )

    @mock.patch('pyramid_bimt.sanity_check.Group')
    def test_no_warnings(self, Group):
        user = mock.Mock()
        user.id = 2
        user.email = 'foo@bar.com'
        user.fullname = 'Foo'

        from pyramid_bimt.sanity_check import check_user
        self.assertEqual(
            check_user(user),
            [],
        )


class TestSanityCheck(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanity_check.check_admin_user')
    @mock.patch('pyramid_bimt.sanity_check.check_default_groups')
    @mock.patch('pyramid_bimt.sanity_check.check_user')
    @mock.patch('pyramid_bimt.sanity_check.User')
    def test_no_warnings(self, User, check_user, check_default_groups, check_admin_user):  # noqa
        check_admin_user.return_value = []
        check_default_groups.return_value = []
        check_user.return_value = []
        User.get_all.return_value = []

        from pyramid_bimt.sanity_check import sanity_check
        self.assertEqual(sanity_check(), [])

    @mock.patch('pyramid_bimt.sanity_check.check_admin_user')
    @mock.patch('pyramid_bimt.sanity_check.check_default_groups')
    @mock.patch('pyramid_bimt.sanity_check.check_user')
    @mock.patch('pyramid_bimt.sanity_check.User')
    def test_some_warnings(self, User, check_user, check_default_groups, check_admin_user):  # noqa
        check_admin_user.return_value = ['admin warning', ]
        check_default_groups.return_value = ['groups warning', ]
        check_user.return_value = ['user warning']
        User.get_all.return_value = ['user1', 'user2']

        from pyramid_bimt.sanity_check import sanity_check
        self.assertEqual(
            sanity_check(),
            [
                'admin warning',
                'groups warning',
                'user warning',
                'user warning',
            ],
        )


class TestSanityCheckView(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        self.request = testing.DummyRequest()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.sanity_check.sanity_check')
    @mock.patch('pyramid_bimt.sanity_check.app_assets')
    def test_assets(self, app_assets, sanity_check):
        sanity_check.return_value = []

        from pyramid_bimt.sanity_check import sanity_check_view
        sanity_check_view(self.request)
        app_assets.need.assert_called_with()

    @mock.patch('pyramid_bimt.sanity_check.sanity_check')
    def test_view_result(self, sanity_check):
        sanity_check.return_value = ['warning1', 'warning2']

        from pyramid_bimt.sanity_check import sanity_check_view
        result = sanity_check_view(self.request)
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

    @mock.patch('pyramid_bimt.scripts.sanity_check_email.sanity_check')
    def test_no_warnings(self, sanity_check):
        sanity_check.return_value = []

        from pyramid_bimt.scripts.sanity_check_email import send_email
        send_email(self.config.registry.settings, self.request)

        mailer = get_mailer(self.config)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].recipients, ['maintenance@niteoweb.com', ])
        self.assertEqual(
            mailer.outbox[0].subject, u'BIMT sanity check OK')
        self.assertIn(
            'Everything in order, nothing to report.', mailer.outbox[0].html)

    @mock.patch('pyramid_bimt.scripts.sanity_check_email.sanity_check')
    def test_some_warnings(self, sanity_check):
        sanity_check.return_value = ['warning1', 'warning2']

        from pyramid_bimt.scripts.sanity_check_email import send_email
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
