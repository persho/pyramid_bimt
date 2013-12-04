# -*- coding: utf-8 -*-
"""Tests for the expire_subscriptions script."""

from pyramid import testing
from datetime import date
from pyramid_bimt.scripts.expire_subscriptions import expire_subscriptions

import mock
import unittest


class TestExpireSubscriptions(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_user(self, enabled=True, valid_to=None):
        user = mock.Mock(spec='enabled disable valid_to'.split())
        user.id = 1
        user.enabled = enabled
        user.valid_to = valid_to
        return user

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_disable_expired_member(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 29))
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        user.disable.assert_called_with()

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_skip_already_disabled_member(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 29), enabled=False)
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        with self.assertRaises(AssertionError) as cm:
            user.disable.assert_called_with()

        self.assertEqual(
            cm.exception.message, 'Expected call: disable()\nNot called')

    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.User')
    @mock.patch('pyramid_bimt.scripts.expire_subscriptions.date')
    def test_skip_valid_subscription(self, mocked_date, User):
        mocked_date.today.return_value = date(2013, 12, 30)
        user = self._make_user(valid_to=date(2013, 12, 31))
        User.get_all.return_value = [user, ]

        expire_subscriptions()
        with self.assertRaises(AssertionError) as cm:
            user.disable.assert_called_with()

        self.assertEqual(
            cm.exception.message, 'Expected call: disable()\nNot called')
