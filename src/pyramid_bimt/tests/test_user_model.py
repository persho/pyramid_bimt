# -*- coding: utf-8 -*-
"""Tests for the User model."""

from datetime import date
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB
from sqlalchemy.exc import IntegrityError

import unittest


def _make_user(email='foo@bar.com', **kwargs):
    user = User(email=email, **kwargs)
    Session.add(user)
    return user


class TestUserModel(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(groups=True, users=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_default_values(self):
        user = _make_user()
        Session.flush()
        self.assertEqual(user.valid_to, date.today())

    def test_email_is_unique(self):
        _make_user(email='foo@bar.com')
        _make_user(email='foo@bar.com')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn('column email is not unique', cm.exception.message)

    def test_billing_email_is_unique(self):
        _make_user(billing_email='foo@bar.com')
        _make_user(billing_email='foo@bar.com')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn(
            'column billing_email is not unique', cm.exception.message)


class TestUserById(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id(self):
        self.assertEqual(User.by_id(1), None)
        self.assertEqual(User.by_id('foo'), None)
        self.assertEqual(User.by_id(None), None)

    def test_valid_id(self):
        _make_user(email='foo@bar.com')
        user = User.by_id(1)
        self.assertEqual(user.email, 'foo@bar.com')


class TestUserByEmail(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_email(self):
        self.assertEqual(User.by_email(1), None)
        self.assertEqual(User.by_email('foo@bar.com'), None)
        self.assertEqual(User.by_email(None), None)

    def test_valid_email(self):
        _make_user(email='foo@bar.com')
        user = User.by_email(email='foo@bar.com')
        self.assertEqual(user.email, 'foo@bar.com')


class TestUserGetAll(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_servers(self):
        users = User.get_all().all()
        self.assertEqual(len(users), 0)

    def test_all_users(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all().all()
        self.assertEqual(len(users), 3)

    def test_ordered_by_email_by_default(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all().all()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].email, 'bar@bar.com')
        self.assertEqual(users[1].email, 'baz@bar.com')
        self.assertEqual(users[2].email, 'foo@bar.com')

    def test_override_ordered_by(self):
        _make_user(email='foo@bar.com', fullname=u'A')
        _make_user(email='bar@bar.com', fullname=u'C')
        _make_user(email='baz@bar.com', fullname=u'B')
        users = User.get_all(order_by='fullname').all()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].fullname, 'A')
        self.assertEqual(users[1].fullname, 'B')
        self.assertEqual(users[2].fullname, 'C')

    def test_filter_by(self):
        _make_user(email='foo@bar.com', affiliate=u'John')
        _make_user(email='bar@bar.com', affiliate=u'Jane')
        users = User.get_all(filter_by={'affiliate': u'John'}).all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].affiliate, 'John')

    def test_limit(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        users = User.get_all(limit=1).all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'bar@bar.com')


class TestAdmin(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_is_admin(self):
        self.assertTrue(User.by_email('admin@bar.com').admin)

    def test_user_is_not_admin(self):
        self.assertFalse(User.by_email('one@bar.com').admin)


class TestTrial(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_is_trial(self):
        self.assertTrue(User.by_email('one@bar.com').trial)

    def test_user_is_not_trial(self):
        self.assertFalse(User.by_email('admin@bar.com').trial)


class TestEnabledDisabled(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()
        self.user = _make_user()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_enable(self):
        self.assertFalse(self.user.enabled)
        self.user.enable()
        self.assertTrue(self.user.enabled)

    def test_user_disable(self):
        self.test_user_enable()
        self.assertTrue(self.user.enabled)
        self.user.disable()
        self.assertFalse(self.user.enabled)

    def test_get_enabled(self):
        enabled = User.get_enabled()
        self.assertEqual(len(enabled), 2)
        self.assertItemsEqual(
            [user.email for user in enabled],
            ['admin@bar.com', 'one@bar.com'],
        )


class TestUserProperties(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.user = _make_user()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_get_property(self):
        with self.assertRaises(KeyError) as cm:
            self.user.get_property('foo')
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')

    def test_get_property_with_default_value(self):
        self.assertEqual(
            self.user.get_property('foo', default=u'bar'), u'bar',)

    def test_set_property(self):
        self.user.set_property('foo', u'bar')
        self.assertEqual(self.user.get_property('foo'), u'bar')

        self.user.set_property('foo', u'baz')
        self.assertEqual(self.user.get_property('foo'), u'baz')

    def test_set_property_strict(self):
        with self.assertRaises(KeyError) as cm:
            self.user.set_property('foo', u'bar', strict=True)
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')
