# -*- coding: utf-8 -*-
"""Misc and tools tests."""

from pyramid import testing

import mock
import unittest


class TestCheckSettings(unittest.TestCase):

    def setUp(self):
        self.settings_full = {
            'authtkt.secret': '',
            'bimt.app_name': 'bimt',
            'bimt.app_secret': '',
            'bimt.app_title': 'BIMT',
            'bimt.disabled_user_redirect_path': '',
            'bimt.payment_reminders': '',
            'bimt.pricing_page_url': '',
            'mail.info_address': '',
            'script_location': '',
            'session.secret': '',
            'sqlalchemy.url': '',
        }
        self.config_full = testing.setUp(settings=self.settings_full)

        self.settings_full_production = self.settings_full.copy()
        self.settings_full_production.update({
            'bimt.jvzoo_regular_period': '',
            'bimt.jvzoo_secret_key': '',
            'bimt.jvzoo_trial_period': '',
            'bimt.piwik_site_id': '',
            'mail.default_sender': 'test@xyz.xyz',
            'mail.host': '',
            'mail.password': '',
            'mail.port': '',
            'mail.tls': '',
            'mail.username': '',
        })
        self.config_full_production = testing.setUp(
            settings=self.settings_full_production)

        self.config_empty = testing.setUp(settings={})

        self.settings_missing = self.settings_full.copy()
        del self.settings_missing['bimt.app_name']
        self.config_missing = testing.setUp(settings=self.settings_missing)

    def tearDown(self):
        testing.tearDown()

    def test_check_required_settings(self):
        from pyramid_bimt import check_required_settings

        try:
            check_required_settings(self.config_full)
        except KeyError as ke:  # pragma: no cover
            self.fail(ke.message)

    def test_empty_required_settings(self):
        from pyramid_bimt import check_required_settings
        with self.assertRaises(KeyError):
            check_required_settings(self.config_empty)

    def test_missing_required_settings(self):
        from pyramid_bimt import check_required_settings

        with self.assertRaises(KeyError) as cm:
            check_required_settings(self.config_missing)

        self.assertIn('bimt.app_name', cm.exception.message)

    @mock.patch('pyramid_bimt.sys')
    def test_check_required_settings_production(self, patched_sys):
        from pyramid_bimt import check_required_settings

        patched_sys.argv = ['pserve', 'production.ini']

        try:
            check_required_settings(self.config_full_production)
        except KeyError as ke:  # pragma: no cover
            self.fail(ke.message)

    @mock.patch('pyramid_bimt.sys')
    def test_empty_required_settings_production(self, patched_sys):
        from pyramid_bimt import check_required_settings
        patched_sys.argv = ['pserve', 'production.ini']
        with self.assertRaises(KeyError):
            check_required_settings(self.config_empty)

    @mock.patch('pyramid_bimt.sys')
    def test_missing_required_settings_production(self, patched_sys):
        from pyramid_bimt import check_required_settings

        patched_sys.argv = ['pserve', 'production.ini']

        with self.assertRaises(KeyError) as cm:
            check_required_settings(self.config_full)

        self.assertIn('bimt.jvzoo_regular_period', cm.exception.message)


class TestExceptions(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_workflow_exception(self):
        from pyramid_bimt.exc import WorkflowError

        we = WorkflowError(msg='test message')
        self.assertEqual(we.__str__(), 'test message')


class TestSanityCheck(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.misc.send_sanity_mail')
    def test_sanity_check_secret(self, mail):
        from pyramid_bimt.views.misc import bimt_sanity_check

        req = mock.Mock()
        req.GET = {'secret': 'secret'}
        req.registry.settings = {'bimt.app_secret': 'secret'}
        view = bimt_sanity_check(req)
        self.assertEqual(view['title'], 'Sanity check')
        self.assertEqual(
            view['form'],
            '<p>Sanity check finished and mail sent</p>'
        )

    @mock.patch('pyramid_bimt.views.misc.send_sanity_mail')
    def test_sanity_check_admin(self, mail):
        from pyramid_bimt.views.misc import bimt_sanity_check

        req = mock.Mock()
        req.GET = {}
        req.user = mock.Mock()
        group = mock.Mock()
        group.name.return_value = 'admins'
        req.user.groups = [group, ]

        view = bimt_sanity_check(req)
        self.assertEqual(view['title'], 'Not Allowed')
        self.assertEqual(
            view['form'],
            '<p>Not Allowed</p>'
        )

    def test_check_user_enabled_trial(self):
        from pyramid_bimt.views.misc import check_user
        user = mock.Mock()
        user.enabled = True
        user.trial = True
        user.regular = False
        self.assertEqual(len(check_user(user)), 0)

    def test_check_user_disabled_trial(self):
        from pyramid_bimt.views.misc import check_user
        user = mock.Mock()
        user.enabled = False
        user.trial = True
        user.regular = False
        user.id = 1
        self.assertEqual(
            check_user(user)[0],
            'User 1 is disabled but in trial group!'
        )

    def test_check_user_disabled_regular(self):
        from pyramid_bimt.views.misc import check_user
        user = mock.Mock()
        user.enabled = False
        user.trial = False
        user.regular = True
        user.id = 1
        self.assertEqual(
            check_user(user)[0],
            'User 1 is disabled but in regular group!'
        )

    def test_check_user_enabled(self):
        from pyramid_bimt.views.misc import check_user
        user = mock.Mock()
        user.enabled = True
        user.trial = False
        user.regular = False
        user.id = 1
        self.assertEqual(
            check_user(user)[0],
            'User 1 is enabled but not trial or regular!'
        )

    def test_check_user_trial_regular(self):
        from pyramid_bimt.views.misc import check_user
        user = mock.Mock()
        user.enabled = True
        user.trial = True
        user.regular = True
        user.id = 1
        self.assertEqual(
            check_user(user)[0],
            'User 1 is both trial and regular!'
        )

    @mock.patch('pyramid_bimt.views.misc.Message')
    @mock.patch('pyramid_bimt.views.misc.check_user')
    @mock.patch('pyramid_bimt.views.misc.User')
    @mock.patch('pyramid_bimt.views.misc.mailer_factory_from_settings')
    def test_send_sanity_mail_errors(self, mailer, user, check_user, msg):
        from pyramid_bimt.views.misc import send_sanity_mail
        from datetime import date
        user.get_all.return_value = ['user1', 'user2']
        check_user.side_effect = [['error1', ], ['error2', ]]

        req = mock.Mock()
        req.registry.settings = {
            'mail.info_address': 'info@bar.com',
            'mail.default_sender': 'sender@bar.com'
        }
        send_sanity_mail(req)

        msg_body = '<table cellpadding="0" cellspacing="0" width="100%" style="color: #000000; font-family: Arial, sans-serif; font-size: 13px; margin-bottom: 5px; text-align: left;" bgcolor="#ffffff">\n    <tr>\n        <td>\n      <table align="left" cellpadding="0" cellspacing="0" width="600">\n        <tr>\n          <td class="body">\n            <!-- begin body -->\n            \n            <p>\n                Your application has the following errors:\n            </p>\n            <table>\n                <tr>\n                    <td>error1</td>\n                </tr>\n                <tr>\n                    <td>error2</td>\n                </tr>\n            </table>\n            <!-- end body -->\n          </td>\n        </tr>\n      </table>\n        </td>\n    </tr>\n</table>\n'  # noqa

        msg.assert_called_with(
            body=msg_body,
            sender='sender@bar.com',
            recipients=['info@bar.com', ],
            subject='Bimt sanity check errors on day: {}'.format(date.today())
            )

    @mock.patch('pyramid_bimt.views.misc.Message')
    @mock.patch('pyramid_bimt.views.misc.check_user')
    @mock.patch('pyramid_bimt.views.misc.User')
    @mock.patch('pyramid_bimt.views.misc.mailer_factory_from_settings')
    def test_send_sanity_mail_ok(self, mailer, user, check_user, msg):
        from pyramid_bimt.views.misc import send_sanity_mail
        user.get_all.return_value = ['user1', 'user2']
        check_user.side_effect = [[], []]

        req = mock.Mock()
        req.registry.settings = {
            'mail.info_address': 'info@bar.com',
            'mail.default_sender': 'sender@bar.com'
        }
        send_sanity_mail(req)

        msg_body = '<table cellpadding="0" cellspacing="0" width="100%" style="color: #000000; font-family: Arial, sans-serif; font-size: 13px; margin-bottom: 5px; text-align: left;" bgcolor="#ffffff">\n    <tr>\n        <td>\n      <table align="left" cellpadding="0" cellspacing="0" width="600">\n        <tr>\n          <td class="body">\n            <!-- begin body -->\n            <p>\n                Everything in order, all user groups set correctly!\n            </p>\n            \n            \n            <!-- end body -->\n          </td>\n        </tr>\n      </table>\n        </td>\n    </tr>\n</table>\n'  # noqa
        msg.assert_called_with(
            body=msg_body,
            sender='sender@bar.com',
            recipients=['info@bar.com', ],
            subject='Bimt sanity check is OK!'
            )
