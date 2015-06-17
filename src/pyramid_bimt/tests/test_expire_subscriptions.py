# -*- coding: utf-8 -*-
"""Tests for the expire_subscriptions script."""

from datetime import date
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from pyramid_bimt.scripts.expire_subscriptions import expire_subscriptions
from pyramid_bimt.testing import initTestingDB

import mock
import transaction
import unittest


class TestExpireSubscriptions(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_user(self, enabled=True, valid_to=None):
        user = mock.Mock(spec='enabled disable valid_to groups'.split())
        user.id = 1
        user.enabled = enabled
        user.valid_to = valid_to
        user.properties = []
        return user

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_skip_already_disabled_member(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 29), enabled=False)
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        self.assertEqual(user.disable.call_count, 0)

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_skip_valid_subscription(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 31))
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        self.assertEqual(user.disable.call_count, 0)

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_skip_non_valid_to_properties(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 31))
        user.properties = [
            UserProperty(key='foo', value='bar'),
            UserProperty(key='addon_1_last_payment', value='baz'),
        ]
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        self.assertEqual(user.groups.remove.call_count, 0)

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_skip_valid_addon_subscription(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 31))
        user.properties = [
            UserProperty(key='addon_1_valid_to', value='2014-12-31'),
        ]
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        self.assertEqual(user.groups.remove.call_count, 0)


class TestExpireSubscriptionsIntegration(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB(auditlog_types=True, groups=True, users=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_disable_expired_member(self, mocked_date):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = User.by_email('admin@bar.com')
        user.valid_to = date(2013, 12, 29)
        transaction.commit()

        expire_subscriptions()

        user = User.by_email('admin@bar.com')
        self.assertFalse(user.enabled)
        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserDisabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Disabled user admin@bar.com (1) because its '
            u'valid_to (2013-12-29) has expired.',
        )

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_disable_expired_addon(self, mocked_date):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = User.by_email('admin@bar.com')
        user.valid_to = date(2013, 12, 31)
        user.set_property('addon_1_valid_to', date(2013, 12, 29))
        user.groups.append(Group(name='foo', product_id=1))
        transaction.commit()

        expire_subscriptions()

        user = User.by_email('admin@bar.com')
        self.assertTrue(user.enabled)
        self.assertEqual([g.name for g in user.groups], ['admins', 'enabled'])
        self.assertEqual(len(user.audit_log_entries), 1)
        self.assertEqual(
            user.audit_log_entries[0].event_type.name, u'UserDisabled')
        self.assertEqual(
            user.audit_log_entries[0].comment,
            u'Addon "foo" disabled for user admin@bar.com (1) because its '
            u'valid_to (2013-12-29) has expired.',
        )
