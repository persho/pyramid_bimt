# -*- coding: utf-8 -*-
"""Tests for the JVZoo Notification Service integration."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_auth
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.models import User
from datetime import date

import mock
import unittest


class TestJVZooView(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.jvzoo_secret_key': 'secret',
            'bimt.jvzoo_trial_period': 7,
            'bimt.jvzoo_regular_period': 31,
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)

    def tearDown(self):
        testing.tearDown()

    def test_missing_POST(self):
        from pyramid_bimt.views.jvzoo import JVZooView
        request = testing.DummyRequest()
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'No POST request.')

    def test_missing_cverify(self):
        from pyramid_bimt.views.jvzoo import JVZooView
        post = {
            'foo': 'bar',
        }
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(
            resp,
            'POST handling failed: KeyError: cverify',
        )

    def test_invalid_checksum(self):
        from pyramid_bimt.views.jvzoo import JVZooView
        post = {
            'cverify': 'foo',
        }
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(
            resp,
            'POST handling failed: ValueError: Checksum verification failed.',
        )


class TestJVZooViewIntegration(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.jvzoo_secret_key': 'secret',
            'bimt.jvzoo_trial_period': 7,
            'bimt.jvzoo_regular_period': 31,
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        add_routes_auth(self.config)
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def _make_user(
        self,
        email='foo@bms.com',
        billing_email=None,
        enabled=True,
    ):
        user = User(
            email=email,
            password=u'secret',
            billing_email=billing_email,
        )
        Session.add(user)

        if enabled:
            user.enable()

        return user

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    def test_existing_user_new_subscription_payment(self, verify_POST, mocked_date):  # noqa
        from pyramid_bimt.views.jvzoo import JVZooView
        user = self._make_user(email='foo@bms.com')
        post = {
            'ccustemail': 'foo@bms.com',
            'ctransaction': 'BILL',
            'ctransreceipt': 123,

        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True

        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.valid_to, date(2014, 1, 30))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Enabled by JVZoo, transaction id: 123, type: BILL',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    def test_existing_user_cancel_subscription(self, verify_POST, mocked_date):
        from pyramid_bimt.views.jvzoo import JVZooView
        user = self._make_user(email='foo@bms.com')
        post = {
            'ccustemail': 'foo@bms.com',
            'ctransaction': 'RFND',
            'ctransreceipt': 123,
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True

        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, False)
        self.assertEqual(user.valid_to, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserDisabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Disabled by JVZoo, transaction id: 123, type: RFND',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    def test_existing_user_billing_email_and_rejoin(self, verify_POST, mocked_date):  # noqa
        from pyramid_bimt.views.jvzoo import JVZooView
        user = self._make_user(billing_email='bar@bms.com', enabled=False)
        post = {
            'ccustemail': 'bar@bms.com',
            'ctransaction': 'SALE',
            'ctransreceipt': 123,
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True

        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.valid_to, date(2014, 1, 6))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Enabled by JVZoo, transaction id: 123, type: SALE',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    @mock.patch('pyramid_bimt.views.jvzoo.generate')
    def test_new_user(self, generate, verify_POST, mocked_date):
        from pyramid_bimt.views.jvzoo import JVZooView
        post = {
            'ccustemail': 'bar@bms.com',
            'ctransaction': 'SALE',
            'ccustname': 'Foo Bär',
            'ctransreceipt': 123,
            'ctransaffiliate': 'aff@bms.com',
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True
        generate.return_value = 'secret'
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')

        user = User.by_email('bar@bms.com')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.valid_to, date(2014, 1, 6))

        self.assertEqual(len(user.audit_log_entries), 2)

        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserCreated')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Created by JVZoo, transaction id: 123, type: SALE',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by JVZoo, transaction id: 123, type: SALE',
        )

        from pyramid_mailer import get_mailer
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject, u'Welcome to BIMT!')
        self.assertIn('Hello Foo Bär'.decode('utf-8'), mailer.outbox[0].html)
        self.assertIn('u: bar@bms.com', mailer.outbox[0].html)
        self.assertIn('p: secret', mailer.outbox[0].html)
        self.assertIn('BIMT Team', mailer.outbox[0].html)
        self.assertIn(
            '<a href="http://example.com/login">http://example.com/login</a>',
            mailer.outbox[0].html,
        )
