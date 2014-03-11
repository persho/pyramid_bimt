# -*- coding: utf-8 -*-
"""Tests for the JVZoo Notification Service integration."""

from datetime import date
from datetime import timedelta
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_auth
from pyramid_bimt import configure
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB

import mock
import unittest
import webtest


def _make_jvzoo_group():
    group = Group(
        name='monthly',
        product_id=1,
        validity=31,
        trial_validity=7,
    )
    Session.add(group)
    return group


class TestJVZooView(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.jvzoo_secret_key': 'secret',
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
            'POST handling failed: ValueError: Checksum verification failed',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    @mock.patch('pyramid_bimt.views.jvzoo.User')
    @mock.patch('pyramid_bimt.views.jvzoo.Group')
    def test_invalid_product_id(self, Group, User, verify_POST):
        from pyramid_bimt.views.jvzoo import JVZooView
        post = {
            'ccustemail': 'foo@bar.com',
            'ctransaction': 'SALE',
            'cproditem': 123,
        }

        verify_POST.return_value = True
        User.by_email = mock.Mock()
        Group.by_product_id.return_value = None
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(
            resp,
            'POST handling failed: ValueError: Cannot find group with '
            'product_id "123"',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    @mock.patch('pyramid_bimt.views.jvzoo.User')
    @mock.patch('pyramid_bimt.views.jvzoo.Group')
    def test_invalid_transaction_type(self, Group, User, verify_POST):
        from pyramid_bimt.views.jvzoo import JVZooView
        post = {
            'ccustemail': 'foo@bar.com',
            'ctransaction': 'FOO',
            'cproditem': 1,
        }

        verify_POST.return_value = True
        User.by_email = mock.Mock()
        Group.by_product_id.return_value = mock.Mock()
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(
            resp,
            'POST handling failed: ValueError: Unknown Transaction Type: FOO',
        )

    def test_verify_POST(self):
        """Test POST verification process."""
        from pyramid_bimt.views.jvzoo import JVZooView
        post = dict(
            ccustname=u'fullname',
            cverify=u'38CFCDED',
        )
        request = testing.DummyRequest(post=post)
        self.assertTrue(JVZooView(request)._verify_POST())


class TestJVZooViewIntegration(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.jvzoo_secret_key': 'secret',
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        add_routes_auth(self.config)
        initTestingDB(auditlog_types=True, groups=True)
        self.jvzoo_group = _make_jvzoo_group()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def _make_user(
        self,
        email='foo@bar.com',
        billing_email=None,
        enabled=True,
        **kwargs
    ):
        user = User(
            email=email,
            password=u'secret',
            billing_email=billing_email,
            **kwargs
        )
        Session.add(user)

        if enabled:
            user.enable()

        return user

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    def test_existing_user_new_subscription_payment(
        self, verify_POST, mocked_date
    ):
        from pyramid_bimt.views.jvzoo import JVZooView
        user = self._make_user(
            email='foo@bar.com',
            groups=[Group.by_name('enabled'), Group.by_name('trial')],
        )
        post = {
            'ccustemail': 'FOO@bar.com',
            'ctransaction': 'BILL',
            'ctransreceipt': 123,
            'cproditem': 1,

        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True

        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.trial, False)
        self.assertEqual(user.valid_to, date(2014, 1, 30))
        self.assertEqual(user.last_payment, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Enabled by JVZoo, transaction id: 123, type: BILL, note: '
            u'regular until 2014-01-30',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    def test_existing_user_cancel_subscription(self, verify_POST, mocked_date):
        from pyramid_bimt.views.jvzoo import JVZooView
        user = self._make_user(
            email='foo@bar.com',
            groups=[
                Group.by_name('enabled'),
                Group.by_name('trial'),
                Group.by_name('monthly'),
            ])
        post = {
            'ccustemail': 'FOO@bar.com',
            'ctransaction': 'RFND',
            'ctransreceipt': 123,
            'cproditem': 1,
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
            u'Disabled by JVZoo, transaction id: 123, type: RFND, note: '
            u'removed from groups: enabled, trial, monthly',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    def test_existing_user_billing_email_and_rejoin(
        self, verify_POST, mocked_date
    ):
        from pyramid_bimt.views.jvzoo import JVZooView
        user = self._make_user(billing_email='bar@bar.com', enabled=False)
        post = {
            'ccustemail': 'BAR@bar.com',
            'ctransaction': 'SALE',
            'ctransreceipt': 123,
            'cproditem': 1,
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True

        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.trial, True)
        self.assertEqual(user.valid_to, date(2014, 1, 6))
        self.assertEqual(user.last_payment, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Enabled by JVZoo, transaction id: 123, type: SALE, '
            u'note: trial until 2014-01-06',
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    @mock.patch('pyramid_bimt.views.jvzoo.generate')
    def test_new_user_no_trial(self, generate, verify_POST, mocked_date):
        from pyramid_bimt.views.jvzoo import JVZooView
        Group.by_name('monthly').trial_validity = None
        post = {
            'ccustemail': 'BAR@bar.com',
            'ctransaction': 'SALE',
            'ccustname': 'Foo Bär',
            'ctransreceipt': 123,
            'cproditem': 1,
            'ctransaffiliate': 'aff@bar.com',
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True
        generate.return_value = 'secret'
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')

        user = User.by_email('bar@bar.com')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.trial, False)
        self.assertEqual(user.valid_to, date(2014, 1, 30))
        self.assertEqual(user.last_payment, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 2)

        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserCreated')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Created by JVZoo, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by JVZoo, transaction id: 123, type: SALE, note: '
            u'regular until 2014-01-30',
        )

        from pyramid_mailer import get_mailer
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject, u'Welcome to BIMT!')
        self.assertIn('Hello Foo Bär'.decode('utf-8'), mailer.outbox[0].html)
        self.assertIn('u: bar@bar.com', mailer.outbox[0].html)
        self.assertIn('p: secret', mailer.outbox[0].html)
        self.assertNotIn('api:', mailer.outbox[0].html)
        self.assertIn('BIMT Team', mailer.outbox[0].html)
        self.assertIn(
            '<a href="http://example.com/login">http://example.com/login</a>',
            mailer.outbox[0].html,
        )

    @mock.patch('pyramid_bimt.views.jvzoo.date')
    @mock.patch('pyramid_bimt.views.jvzoo.JVZooView._verify_POST')
    @mock.patch('pyramid_bimt.views.jvzoo.generate')
    def test_welcome_email_api_key_sent(self, generate, verify_POST, mocked_date):  # noqa
        from pyramid_bimt.events import IUserCreated

        def generate_api_key2(event):
            event.user.set_property('api_key', u'secret_key')

        self.config.add_subscriber(generate_api_key2, IUserCreated)

        from pyramid_bimt.views.jvzoo import JVZooView
        Group.by_name('monthly').trial_validity = None
        post = {
            'ccustemail': 'BAR@bar.com',
            'ctransaction': 'SALE',
            'ccustname': 'Foo Bär',
            'ctransreceipt': 123,
            'cproditem': 1,
            'ctransaffiliate': 'aff@bar.com',
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True
        generate.return_value = 'secret'
        request = testing.DummyRequest(post=post)
        resp = JVZooView(request).jvzoo()
        self.assertEqual(resp, 'Done.')

        user = User.by_email('bar@bar.com')
        self.assertEqual(user.get_property('api_key', default=u''), u'secret_key')  # noqa
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.trial, False)
        self.assertEqual(user.valid_to, date(2014, 1, 30))
        self.assertEqual(user.last_payment, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 2)

        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserCreated')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Created by JVZoo, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by JVZoo, transaction id: 123, type: SALE, note: '
            u'regular until 2014-01-30',
        )

        from pyramid_mailer import get_mailer
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject, u'Welcome to BIMT!')
        self.assertIn('Hello Foo Bär'.decode('utf-8'), mailer.outbox[0].html)
        self.assertIn('u: bar@bar.com', mailer.outbox[0].html)
        self.assertIn('p: secret', mailer.outbox[0].html)
        self.assertIn('API key: secret_key', mailer.outbox[0].html)
        self.assertIn('BIMT Team', mailer.outbox[0].html)
        self.assertIn(
            '<a href="http://example.com/login">http://example.com/login</a>',
            mailer.outbox[0].html,
        )


class TestJVZooViewFunctional(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
            'bimt.jvzoo_secret_key': 'secret',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        initTestingDB(auditlog_types=True, groups=True)
        _make_jvzoo_group()
        configure(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_create_new_user(self):
        post = {
            'ccustname': 'John Smith',
            'ccustemail': 'John.Smith@email.com',
            'ctransaction': 'SALE',
            'ctransaffiliate': 'Affiliate@email.com',
            'ctransreceipt': 123,
            'cproditem': 1,
            'cverify': 'F718EC5F',
        }
        resp = self.testapp.post('/jvzoo', params=post, status=200)
        self.assertEqual('Done.', resp.text)

        user = User.by_email('john.smith@email.com')
        self.assertEqual(user.fullname, 'John Smith')
        self.assertEqual(user.affiliate, 'affiliate@email.com')
        self.assertEqual(user.trial, True)
        self.assertEqual(user.valid_to, date.today() + timedelta(days=7))
        self.assertEqual(user.last_payment, date.today())
        self.assertTrue(user.enabled)

        self.assertEqual(len(user.audit_log_entries), 2)

        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserCreated')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Created by JVZoo, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by JVZoo, transaction id: 123, type: SALE, note: trial until {}'.format(  # noqa
                date.today() + timedelta(days=7)),
        )

        from pyramid_mailer import get_mailer
        mailer = get_mailer(testing.DummyRequest())
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject, u'Welcome to BIMT!')
        self.assertIn('Hello John Smith', mailer.outbox[0].html)
        self.assertIn('u: john.smith@email.com', mailer.outbox[0].html)
        self.assertNotIn('API', mailer.outbox[0].html)
        self.assertRegexpMatches(mailer.outbox[0].html, 'p: .{10}\n')
        self.assertIn('BIMT Team', mailer.outbox[0].html)
        self.assertIn(
            '<a href="http://localhost/login">http://localhost/login</a>',
            mailer.outbox[0].html,
        )
