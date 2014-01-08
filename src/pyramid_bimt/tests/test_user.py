# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB

import unittest


class TestUserView(unittest.TestCase):
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