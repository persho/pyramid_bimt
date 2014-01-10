# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB

import unittest


class TestUserModel(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        initTestingDB(groups=True, users=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_set_get_properties(self):
        from pyramid_bimt.models import User
        user = User.by_email('one@bar.com')

        with self.assertRaises(ValueError):
            user.get_property('test')
        self.assertEquals(
            user.get_property('test', default=u'test_value'),
            u'test_value',
        )

        with self.assertRaises(ValueError):
            user.set_property('test', u'test_value', strict=True)
        user.set_property('test', u'test_value')

        self.assertEquals(user.get_property('test'), u'test_value')
        user.set_property('test', u'test_value2')
        self.assertEquals(user.get_property('test'), u'test_value2')

    def test_user_admin(self):
        from pyramid_bimt.models import User
        self.assertFalse(User.by_email('one@bar.com').admin)
        self.assertTrue(User.by_email('admin@bar.com').admin)

    def test_user_get_all(self):
        from pyramid_bimt.models import User
        self.assertIsNotNone(User.get_all())
        self.assertEquals(User.get_all().count(), 2)
        self.assertIsNotNone(User.get_all(filter_by={'email': 'one@bar.com'}))
        self.assertEquals(User.get_all(filter_by={'email': 'foo'}).count(), 0)

    def test_user_get_enabled(self):
        from pyramid_bimt.models import User
        self.assertIsNotNone(User.get_enabled())
        self.assertEquals(len(User.get_enabled()), 2)

    def test_user_trial(self):
        from pyramid_bimt.models import User
        user = User.by_email('one@bar.com')
        self.assertFalse(user.trial)
        self.assertTrue(user.set_trial())
        self.assertTrue(user.trial)
        self.assertFalse(user.set_trial())

        self.assertTrue(user.disable())
        self.assertFalse(user.trial)

    def test_user_trial_not_enabled(self):
        from pyramid_bimt.exc import WorkflowError
        from pyramid_bimt.models import User
        user = User.by_email('one@bar.com')
        user.disable()
        self.assertFalse(user.enabled)
        self.assertFalse(user.trial)
        with self.assertRaises(WorkflowError):
            user.set_trial()

    def test_user_regular(self):
        from pyramid_bimt.models import User
        user = User.by_email('one@bar.com')
        self.assertFalse(user.regular)
        self.assertTrue(user.set_regular())
        self.assertTrue(user.regular)
        self.assertFalse(user.set_regular())

        self.assertTrue(user.disable())
        self.assertFalse(user.regular)

    def test_user_regular_not_enabled(self):
        from pyramid_bimt.exc import WorkflowError
        from pyramid_bimt.models import User
        user = User.by_email('one@bar.com')
        user.disable()
        self.assertFalse(user.enabled)
        self.assertFalse(user.regular)
        with self.assertRaises(WorkflowError):
            user.set_regular()
