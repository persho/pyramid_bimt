# -*- coding: utf-8 -*-
"""Tests for referral view."""

from pyramid import testing
from pyramid.threadlocal import get_current_request
from pyramid_basemodel import Session
from pyramid_bimt import configure
from pyramid_bimt.events import ReferralEmailSent
from pyramid_bimt.views.referrals import ReferralsView

import colander
import mock
import unittest


class TestEmailsValidator(unittest.TestCase):
    def test_valid_emails(self):
        from pyramid_bimt.views.referrals import emails_validator

        self.assertIsNone(
            emails_validator(mock.Mock(), 'foo@bar.com\nbla@foo.com'))

    def test_invalid_emails(self):
        from pyramid_bimt.views.referrals import emails_validator

        with self.assertRaises(colander.Invalid):
            emails_validator(mock.Mock(), 'foo\nbar')


class TestReferralsSettingsView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(request=testing.DummyRequest())
        configure(self.config)
        self.request = get_current_request()

        from pyramid_layout.layout import LayoutManager

        self.request.layout_manager = LayoutManager('context', 'requestr')

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_referrals_view(self):
        request = testing.DummyRequest()
        request.context = mock.Mock()
        request.user = mock.Mock()
        resp = ReferralsView(request)
        self.assertEqual(resp.title, 'Send Referral Invites')

    def test_view_csrf_token(self):
        csrf_token_field = ReferralsView.schema.get('csrf_token')
        self.assertIsNotNone(csrf_token_field)
        self.assertEqual(csrf_token_field.title, 'Csrf Token')

    @mock.patch.object(ReferralEmailSent, 'log_event')
    @mock.patch('pyramid_bimt.views.referrals.Message')
    @mock.patch('pyramid_bimt.views.referrals.Mailer')
    def test_send_invites_success(self, Mailer, Message, log_event):
        from pyramid_bimt.tests.test_user_views import _make_user
        request = testing.DummyRequest()
        self.request.registry.notify = mock.Mock()
        request.registry.settings = {
            'bimt.app_title': u'bimt',
            'mail.host': 'mailhost.com',
            'mail.port': '123',
            'bimt.referrals_mail_username': 'username',
            'bimt.referrals_mail_password': 'password',
            'bimt.referrals_mail_sender': 'sender@mail.com',
            'bimt.referral_url': 'http://www.bimt.com/referral',
        }
        request.user = _make_user()
        appstruct = {'emails': 'foo@bar.com\nbar@foo.com'}

        ReferralsView(request).send_invites_success(appstruct)

        Mailer.assert_called_with(
            host='mailhost.com',
            port='123',
            username='username',
            password='password',
            tls=True,
            default_sender='sender@mail.com',
        )
        html = (u'Hi,\n\nyour friend has invited you to bimt\n\n>>> Visit '
                '<a href="http://example.com">\nbimt</a>\n\nbimt '
                'Team,\n')
        Message.assert_any_call(
            subject=u'Your friend, Foö Bar, gave you exclusive access to bimt',
            recipients=['foo@bar.com', ],
            html=html)
        Message.assert_any_call(
            subject=u'Your friend, Foö Bar, gave you exclusive access to bimt',
            recipients=['bar@foo.com', ],
            html=html)
        self.assertEqual(Mailer.return_value.send.call_count, 2)
        self.assertTrue(self.request.registry.notify.call_count, 2)
