# -*- coding: utf-8 -*-
"""Tests for the JVZoo and ClickBank IPN service integration."""

from datetime import date
from datetime import timedelta
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_auth
from pyramid_bimt import configure
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.views.ipn import AttrDict
from pyramid_bimt.views.ipn import IPNView
from pyramid_mailer import get_mailer
from zope.testing.loggingsupport import InstalledHandler

import json
import mock
import unittest
import webtest

handler = InstalledHandler('pyramid_bimt.views.ipn')


def _make_ipn_group():
    group = Group(
        name='monthly',
        product_id=1,
        validity=31,
        trial_validity=7,
    )
    Session.add(group)
    return group


class TestJVZoo(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.jvzoo_secret_key': 'secret',
        }
        self.config = testing.setUp(settings=settings)

    def test_no_POST(self):
        request = testing.DummyRequest()
        view = IPNView(request)
        with self.assertRaises(ValueError) as cm:
            view.jvzoo()
        self.assertEqual(cm.exception.message, 'No POST request.')

    def test_missing_cverify(self):
        post = {
            'foo': 'bar',
        }
        view = IPNView(testing.DummyRequest(post=post))
        with self.assertRaises(KeyError) as cm:
            view.jvzoo()
        self.assertEqual(
            repr(cm.exception),
            'KeyError(\'cverify\',)',
        )

    def test_invalid_checksum(self):
        post = {
            'cverify': 'foo',
        }
        view = IPNView(testing.DummyRequest(post=post))
        with self.assertRaises(ValueError) as cm:
            view.jvzoo()
        self.assertEqual(
            str(cm.exception),
            'Checksum verification failed',
        )


class TestClickbank(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.clickbank_secret_key': 'secret',
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)

    def test_no_JSON(self):
        request = testing.DummyRequest()
        view = IPNView(request)
        with self.assertRaises(ValueError) as cm:
            view.clickbank()
        self.assertEqual(cm.exception.message, 'No JSON request.')

    def test_invalid_decryption(self):
        request = testing.DummyRequest()
        request.json_body = {
            'iv': '27CD0D0CA9379D32'.encode('base64'),
            'notification': 'bar4567890123456'.encode('base64'),
        }
        view = IPNView(request)
        with self.assertRaises(ValueError) as cm:
            view.clickbank()
        self.assertIn('Decryption failed: ', cm.exception.message)


class TestIPNHandler(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.ipn.IPNView._parse_request_jvzoo')
    @mock.patch('pyramid_bimt.views.ipn.User')
    @mock.patch('pyramid_bimt.views.ipn.Group')
    def test_invalid_product_id(self, Group, User, parse_request):
        parse_request.return_value = None
        User.by_email = mock.Mock()
        Group.by_product_id.return_value = None
        request = testing.DummyRequest(post={'foo': 'bar'})

        view = IPNView(request)
        view.params = AttrDict({
            'email': 'foo@bar.com',
            'product_id': 123,
        })

        with self.assertRaises(ValueError) as cm:
            view.ipn()
        self.assertEqual(
            str(cm.exception),
            'Cannot find group with product_id "123"',
        )

    @mock.patch('pyramid_bimt.views.ipn.requests.post')
    @mock.patch('pyramid_bimt.views.ipn.UserDisabled')
    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_transaction')
    @mock.patch('pyramid_bimt.views.ipn.IPNView._parse_request_jvzoo')
    @mock.patch('pyramid_bimt.views.ipn.User')
    @mock.patch('pyramid_bimt.views.ipn.Group')
    def test_forward_ipn_url(
        self,
        Group,
        User,
        parse_request,
        ipn_transaction,
        UserDisabled,
        request_post,
    ):
        parse_request.return_value = None
        ipn_transaction.return_value = None
        group_mock = mock.Mock()
        group_mock.name = 'test'
        group_mock.forward_ipn_to_url = 'http://www.example.com'
        Group.by_product_id.return_value = group_mock
        User.by_email.return_value = mock.Mock(groups=[group_mock, ])
        request = testing.DummyRequest(post={'foo': 'bar'})
        request.registry = mock.Mock()

        view = IPNView(request)
        view.params = AttrDict({
            'email': 'foo@bar.com',
            'product_id': 123,
        })

        view.ipn()
        request_post.assert_called_with(
            'http://www.example.com',
            params={'foo': 'bar'},
        )


class TestIpnTransaction(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.user = mock.Mock()
        self.group = mock.Mock()
        self.view = IPNView(request=testing.DummyRequest())
        self.view.params = AttrDict()

    def tearDown(self):
        handler.clear()
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_sale_transaction')
    def test_SALE(self, sale_transaction):
        self.view.params.trans_type = 'SALE'
        self.view.ipn_transaction(self.user, self.group)
        sale_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_sale_transaction')
    def test_TEST_SALE(self, sale_transaction):
        self.view.params.trans_type = 'TEST_SALE'
        self.view.ipn_transaction(self.user, self.group)
        sale_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_bill_transaction')
    def test_BILL(self, bill_transaction):
        self.view.params.trans_type = 'BILL'
        self.view.ipn_transaction(self.user, self.group)
        bill_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_bill_transaction')
    def test_TEST_BILL(self, bill_transaction):
        self.view.params.trans_type = 'TEST_BILL'
        self.view.ipn_transaction(self.user, self.group)
        bill_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_disable_transaction')
    def test_RFND(self, disable_transaction):
        self.view.params.trans_type = 'RFND'
        self.view.ipn_transaction(self.user, self.group)
        disable_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_disable_transaction')
    def test_CGBK(self, disable_transaction):
        self.view.params.trans_type = 'CGBK'
        self.view.ipn_transaction(self.user, self.group)
        disable_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_disable_transaction')
    def test_TEST_RFND(self, disable_transaction):
        self.view.params.trans_type = 'TEST_RFND'
        self.view.ipn_transaction(self.user, self.group)
        disable_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_disable_transaction')
    def test_INSF(self, disable_transaction):
        self.view.params.trans_type = 'INSF'
        self.view.ipn_transaction(self.user, self.group)
        self.assertEqual(len(handler.records), 1)
        self.assertEqual(
            handler.records[0].message,
            'Don\'t do anything, user will be disabled when it\'s '
            'subscription runs out.',
        )

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_disable_transaction')
    def test_CANCEL_REBILL(self, disable_transaction):
        self.view.params.trans_type = 'CANCEL-REBILL'
        self.view.ipn_transaction(self.user, self.group)
        self.assertEqual(len(handler.records), 1)
        self.assertEqual(
            handler.records[0].message,
            'Don\'t do anything, user will be disabled when it\'s '
            'subscription runs out.',
        )

    def test_invalid(self):
        self.view.params.trans_type = 'foo'
        with self.assertRaises(ValueError) as cm:
            self.view.ipn_transaction(self.user, self.group)
        self.assertEqual(
            str(cm.exception),
            'Unknown Transaction Type: foo',
        )


class TestIPNViewIntegration(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        self.mailer = get_mailer(testing.DummyRequest())
        add_routes_auth(self.config)
        initTestingDB(auditlog_types=True, groups=True, mailings=True)
        self.ipn_group = _make_ipn_group()

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

    @mock.patch('pyramid_bimt.views.ipn.date')
    def test_existing_trial_user_new_subscription_payment(
        self, mocked_date, user=None
    ):
        if not user:
            user = self._make_user(
                email='foo@bar.com',
                groups=[Group.by_name('enabled'), Group.by_name('trial')],
            )

        mocked_date.today.return_value = date(2013, 12, 30)
        view = IPNView(testing.DummyRequest())
        view.provider = 'jvzoo'
        view.params = AttrDict({
            'email': 'foo@bar.com',
            'fullname': u'Föo Bar',
            'trans_type': 'BILL',
            'trans_id': 123,
            'product_id': 1,
        })

        resp = view.ipn()
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
            u'Enabled by jvzoo, transaction id: 123, type: BILL, note: '
            u'regular until 2014-01-30',
        )

    def test_existing_regular_user_new_subscription_payment(self):
        """Test for the "ValueError: list.remove(x): x not in list" bug."""
        user = self._make_user(
            email='foo@bar.com',
            groups=[Group.by_name('enabled')],
        )
        self.test_existing_trial_user_new_subscription_payment(user=user)

    @mock.patch('pyramid_bimt.views.ipn.date')
    def test_existing_user_cancel_subscription(self, mocked_date):
        user = self._make_user(
            email='foo@bar.com',
            groups=[
                Group.by_name('enabled'),
                Group.by_name('trial'),
                Group.by_name('monthly'),
            ])
        mocked_date.today.return_value = date(2013, 12, 30)

        view = IPNView(testing.DummyRequest())
        view.provider = 'clickbank'
        view.params = AttrDict({
            'email': 'foo@bar.com',
            'trans_type': 'RFND',
            'trans_id': 123,
            'product_id': 1,
        })
        resp = view.ipn()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, False)
        self.assertEqual(user.valid_to, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserDisabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Disabled by clickbank, transaction id: 123, type: RFND, note: '
            u'removed from groups: enabled, trial, monthly',
        )

    @mock.patch('pyramid_bimt.views.ipn.date')
    def test_existing_user_billing_email_and_rejoin(self, mocked_date):
        user = self._make_user(billing_email='bar@bar.com', enabled=False)
        mocked_date.today.return_value = date(2013, 12, 30)

        view = IPNView(testing.DummyRequest())
        view.provider = 'jvzoo'
        view.params = AttrDict({
            'email': 'bar@bar.com',
            'trans_type': 'SALE',
            'trans_id': 123,
            'product_id': 1,
        })

        resp = view.ipn()
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
            u'Enabled by jvzoo, transaction id: 123, type: SALE, '
            u'note: trial until 2014-01-06',
        )

    @mock.patch('pyramid_bimt.views.ipn.date')
    def test_new_user_no_trial(self, mocked_date):
        Group.by_name('monthly').trial_validity = None
        mocked_date.today.return_value = date(2013, 12, 30)

        view = IPNView(testing.DummyRequest())
        view.provider = 'clickbank'
        view.params = AttrDict({
            'email': 'bar@bar.com',
            'fullname': u'Föo Bar',
            'trans_type': 'SALE',
            'trans_id': 123,
            'product_id': 1,
            'affiliate': 'aff@bar.com',
        })
        resp = view.ipn()
        self.assertEqual(resp, 'Done.')

        user = User.by_email('bar@bar.com')
        self.assertEqual(user.enabled, True)
        self.assertEqual(user.trial, False)
        self.assertEqual(user.affiliate, 'aff@bar.com')
        self.assertEqual(user.valid_to, date(2014, 1, 30))
        self.assertEqual(user.last_payment, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 2)

        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserCreated')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Created by clickbank, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by clickbank, transaction id: 123, type: SALE, note: '
            u'regular until 2014-01-30',
        )

    def test_welcome_email_api_key_set(self):
        from pyramid_bimt.events import IUserCreated

        def generate_api_key(event):
            event.user.set_property('api_key', u'secret_key')

        self.config.add_subscriber(generate_api_key, IUserCreated)

        self.test_new_user_no_trial()


class TestJVZooViewFunctional(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
            'bimt.jvzoo_secret_key': 'secret',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        initTestingDB(auditlog_types=True, groups=True, mailings=True)
        _make_ipn_group()
        configure(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)
        self.mailer = get_mailer(testing.DummyRequest())

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
        resp = self.testapp.post('/jvzoo/', params=post, status=200)
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
            u'Created by jvzoo, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by jvzoo, transaction id: 123, type: SALE, note: trial until {}'.format(  # noqa
                date.today() + timedelta(days=7)),
        )
        self.assertEqual(len(self.mailer.outbox), 1)
        self.assertEqual(self.mailer.outbox[0].subject, u'Welcome to BIMT!')
        self.assertIn(u'Hello John Smith', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'here are your login details for the membership area', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'u: john.smith@email.com', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'p: ', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'Best wishes', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'<a href="http://blog.bigimtoolbox.com/">visit our blog</a>', self.mailer.outbox[0].html)  # noqa


class TestClickBankViewFunctional(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
            'bimt.clickbank_secret_key': 'secret',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        initTestingDB(auditlog_types=True, groups=True, mailings=True)
        _make_ipn_group()
        configure(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)
        self.mailer = get_mailer(testing.DummyRequest())

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_create_new_user(self):
        payload = {
            'receipt': '123',
            'transactionType': 'SALE',
            'affiliate': 'aff',
            'lineItems': [
                {'itemNo': '1', 'productTitle': 'A passed in title'},
            ],
            'customer': {
                'billing': {
                    'fullName': 'John Smith',
                    'email': 'John.Smith@email.com',
                },
            }
        }
        payload = json.dumps(payload)
        payload = payload + '\x01\x06\x07\x0b'  # so length is a multiple of 16

        from Crypto.Cipher import AES
        import hashlib
        sha1 = hashlib.sha1()
        sha1.update('secret')
        iv = '27CD0D0CA9379D32'
        cipher = AES.new(sha1.hexdigest()[:32], AES.MODE_CBC, iv)
        encrypted_payload = cipher.encrypt(payload)

        post = {
            'iv': iv.encode('base64'),
            'notification': encrypted_payload.encode('base64'),
        }
        resp = self.testapp.post_json('/clickbank/', post)
        self.assertEqual('Done.', resp.text)

        user = User.by_email('john.smith@email.com')
        self.assertEqual(user.fullname, 'John Smith')
        self.assertEqual(user.affiliate, 'aff')
        self.assertEqual(user.trial, True)
        self.assertEqual(user.valid_to, date.today() + timedelta(days=7))
        self.assertEqual(user.last_payment, date.today())
        self.assertTrue(user.enabled)

        self.assertEqual(len(user.audit_log_entries), 2)

        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserCreated')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Created by clickbank, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by clickbank, transaction id: 123, type: SALE, note: trial until {}'.format(  # noqa
                date.today() + timedelta(days=7)),
        )
        self.assertEqual(len(self.mailer.outbox), 1)
        self.assertEqual(self.mailer.outbox[0].subject, u'Welcome to BIMT!')
        self.assertIn(u'Hello John Smith', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'here are your login details for the membership area', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'u: john.smith@email.com', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'p: ', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'Best wishes', self.mailer.outbox[0].html)  # noqa
        self.assertIn(u'<a href="http://blog.bigimtoolbox.com/">visit our blog</a>', self.mailer.outbox[0].html)  # noqa
