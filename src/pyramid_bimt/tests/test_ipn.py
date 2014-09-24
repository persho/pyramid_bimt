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

import mock
import unittest
import webtest


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
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)

    def test_missing_cverify(self):
        post = {
            'foo': 'bar',
        }
        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
        with self.assertRaises(KeyError) as cm:
            view.ipn()
        self.assertEqual(
            repr(cm.exception),
            'KeyError(\'cverify\',)',
        )

    def test_invalid_checksum(self):
        post = {
            'cverify': 'foo',
        }
        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
        with self.assertRaises(ValueError) as cm:
            view.ipn()
        self.assertEqual(
            str(cm.exception),
            'Checksum verification failed',
        )

    def test_verify_POST(self):
        """Test POST verification process."""
        post = dict(
            ccustname=u'fullname',
            cverify=u'38CFCDED',
        )
        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
        self.assertTrue(view._verify_POST())


class TestIPNHandler(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_missing_POST(self):
        request = testing.DummyRequest()
        resp = IPNView(request).ipn()
        self.assertEqual(resp, 'No POST request.')

    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    @mock.patch('pyramid_bimt.views.ipn.IPNView._map_POST')
    @mock.patch('pyramid_bimt.views.ipn.User')
    @mock.patch('pyramid_bimt.views.ipn.Group')
    def test_invalid_product_id(self, Group, User, map_POST, verify_POST):
        verify_POST.return_value = True
        map_POST.return_value = None
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
    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    @mock.patch('pyramid_bimt.views.ipn.IPNView._map_POST')
    @mock.patch('pyramid_bimt.views.ipn.User')
    @mock.patch('pyramid_bimt.views.ipn.Group')
    def test_forward_ipn_url(
        self,
        Group,
        User,
        map_POST,
        verify_POST,
        ipn_transaction,
        UserDisabled,
        request_post,
    ):
        verify_POST.return_value = True
        map_POST.return_value = None
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
    def test_INSF(self, disable_transaction):
        self.view.params.trans_type = 'INSF'
        self.view.ipn_transaction(self.user, self.group)
        disable_transaction.assert_called_with(self.user, self.group)

    @mock.patch('pyramid_bimt.views.ipn.IPNView.ipn_disable_transaction')
    def test_TEST_RFND(self, disable_transaction):
        self.view.params.trans_type = 'TEST_RFND'
        self.view.ipn_transaction(self.user, self.group)
        disable_transaction.assert_called_with(self.user, self.group)

    def test_invalid(self):
        self.view.params.trans_type = 'foo'
        with self.assertRaises(ValueError) as cm:
            self.view.ipn_transaction(self.user, self.group)
        self.assertEqual(
            str(cm.exception),
            'Unknown Transaction Type: foo',
        )


class TestVerifyPOST(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.view = IPNView(request=testing.DummyRequest())

    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST_jvzoo')
    def test_jvzoo(self, verify_POST_jvzoo):
        self.view.provider = 'jvzoo'
        self.view._verify_POST()
        verify_POST_jvzoo.assert_called_with()

    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST_clickbank')
    def test_clickbank(self, verify_POST_clickbank):
        self.view.provider = 'clickbank'
        self.view._verify_POST()
        verify_POST_clickbank.assert_called_with()

    def test_invalid(self):
        self.view.provider = 'foo'
        with self.assertRaises(ValueError) as cm:
            self.view._verify_POST()
        self.assertEqual(
            str(cm.exception),
            'Unknown provider: foo',
        )


class TestMapPOST(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def test_jvzoo(self):
        post = {
            'ccustname': 'fullname',
            'ccustemail': 'email',
            'cproditem': 'product_id',
            'ctransaction': 'trans_type',
            'ctransreceipt': 'trans_id',
            'ctransaffiliate': 'affiliate',
        }
        view = IPNView(request=testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
        view._map_POST()
        self.assertEqual(
            view.params,
            {
                'product_id': 'product_id',
                'affiliate': 'affiliate',
                'trans_type': 'trans_type',
                'fullname': u'fullname',
                'email': 'email',
                'trans_id': 'trans_id',
            },
        )

    def test_invalid(self):
        view = IPNView(request=testing.DummyRequest())
        view.provider = 'foo'
        with self.assertRaises(ValueError) as cm:
            view._map_POST()
        self.assertEqual(
            str(cm.exception),
            'Unknown provider: foo',
        )


class TestIPNViewIntegration(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.jvzoo_secret_key': 'secret',
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
    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    def test_existing_trial_user_new_subscription_payment(
        self, verify_POST, mocked_date, user=None
    ):
        if not user:
            user = self._make_user(
                email='foo@bar.com',
                groups=[Group.by_name('enabled'), Group.by_name('trial')],
            )

        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True
        post = {
            'ccustemail': 'foo@bar.com',
            'ctransaction': 'BILL',
            'ctransreceipt': 123,
            'cproditem': 1,

        }

        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
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
    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    def test_existing_user_cancel_subscription(self, verify_POST, mocked_date):
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

        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
        resp = view.ipn()
        self.assertEqual(resp, 'Done.')
        self.assertEqual(user.enabled, False)
        self.assertEqual(user.valid_to, date(2013, 12, 30))

        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserDisabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Disabled by jvzoo, transaction id: 123, type: RFND, note: '
            u'removed from groups: enabled, trial, monthly',
        )

    @mock.patch('pyramid_bimt.views.ipn.date')
    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    def test_existing_user_billing_email_and_rejoin(
        self, verify_POST, mocked_date
    ):
        user = self._make_user(billing_email='bar@bar.com', enabled=False)
        post = {
            'ccustemail': 'BAR@bar.com',
            'ctransaction': 'SALE',
            'ctransreceipt': 123,
            'cproditem': 1,
        }
        mocked_date.today.return_value = date(2013, 12, 30)
        verify_POST.return_value = True

        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
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
    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    @mock.patch('pyramid_bimt.views.ipn.generate')
    def test_new_user_no_trial(self, generate, verify_POST, mocked_date):
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
        view = IPNView(testing.DummyRequest(post=post))
        view.provider = 'jvzoo'
        resp = view.ipn()
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
            u'Created by jvzoo, transaction id: 123, type: SALE, note: ',
        )

        self.assertEqual(
            user.audit_log_entries[1].event_type.name, u'UserEnabled')
        self.assertEqual(
            user.audit_log_entries[1].comment,
            u'Enabled by jvzoo, transaction id: 123, type: SALE, note: '
            u'regular until 2014-01-30',
        )

    @mock.patch('pyramid_bimt.views.ipn.date')
    @mock.patch('pyramid_bimt.views.ipn.IPNView._verify_POST')
    @mock.patch('pyramid_bimt.views.ipn.generate')
    def test_welcome_email_api_key_set(
        self, generate, verify_POST, mocked_date
    ):
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
