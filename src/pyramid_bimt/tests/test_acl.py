# -*- coding: utf-8 -*-
"""Tests for the ACL."""

from pyramid import testing

import mock
import unittest


def _make_user():
    return mock.Mock(specs='groups'.split())


def _make_group(name='foo'):
    group = mock.Mock(specs='groups'.split())
    group.name = name
    return group


class TestGroupFinder(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.acl.User')
    def test_no_groups(self, User):
        from pyramid_bimt.acl import groupfinder
        user = _make_user()
        user.groups = []
        User.by_email.return_value = user

        self.assertEqual(groupfinder('foo', self.request), [])

    @mock.patch('pyramid_bimt.acl.User')
    def test_single_group(self, User):
        from pyramid_bimt.acl import groupfinder
        user = _make_user()
        user.groups = [_make_group('foo'), ]
        User.by_email.return_value = user

        self.assertEqual(groupfinder('foo', self.request), ['g:foo'])

    @mock.patch('pyramid_bimt.acl.User')
    def test_multiple_groups(self, User):
        from pyramid_bimt.acl import groupfinder
        user = _make_user()
        user.groups = [_make_group('foo'), _make_group('bar')]
        User.by_email.return_value = user

        self.assertEqual(groupfinder('foo', self.request), ['g:foo', 'g:bar'])


class TestRootFactory(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.acl import RootFactory
        self.factory = RootFactory(self.request)

    def tearDown(self):
        testing.tearDown()

    def test_init(self):
        self.assertIsNotNone(self.factory)
        self.assertEqual(self.factory.request, self.request)


class TestUserFactory(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.acl import UserFactory
        self.factory = UserFactory(self.request)

    def tearDown(self):
        testing.tearDown()

    def test_init(self):
        self.assertIsNotNone(self.factory)
        self.assertEqual(self.factory.request, self.request)

    @mock.patch('pyramid_bimt.acl.User')
    def test_non_existing_user(self, User):
        User.by_id.return_value = None
        with self.assertRaises(KeyError):
            self.factory[0]

    @mock.patch('pyramid_bimt.acl.User')
    def test_existing_user(self, User):
        user = mock.Mock()
        User.by_id.return_value = user
        self.assertEqual(self.factory['foo'], user)
        self.assertEqual(self.factory['foo'].__parent__, self.factory)
        self.assertEqual(self.factory['foo'].__name__, 'foo')


class TestGroupFactory(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.acl import GroupFactory
        self.factory = GroupFactory(self.request)

    def tearDown(self):
        testing.tearDown()

    def test_init(self):
        self.assertIsNotNone(self.factory)
        self.assertEqual(self.factory.request, self.request)

    @mock.patch('pyramid_bimt.acl.Group')
    def test_non_existing_group(self, Group):
        Group.by_id.return_value = None
        with self.assertRaises(KeyError):
            self.factory[0]

    @mock.patch('pyramid_bimt.acl.Group')
    def test_existing_group(self, Group):
        group = mock.Mock()
        Group.by_id.return_value = group
        self.assertEqual(self.factory['foo'], group)
        self.assertEqual(self.factory['foo'].__parent__, self.factory)
        self.assertEqual(self.factory['foo'].__name__, 'foo')


class TestPortletFactory(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.acl import PortletFactory
        self.factory = PortletFactory(self.request)

    def tearDown(self):
        testing.tearDown()

    def test_init(self):
        self.assertIsNotNone(self.factory)
        self.assertEqual(self.factory.request, self.request)

    @mock.patch('pyramid_bimt.acl.Portlet')
    def test_non_existing_portlet(self, Portlet):
        Portlet.by_id.return_value = None
        with self.assertRaises(KeyError):
            self.factory[0]

    @mock.patch('pyramid_bimt.acl.Portlet')
    def test_existing_portlet(self, Portlet):
        portlet = mock.Mock()
        Portlet.by_id.return_value = portlet
        self.assertEqual(self.factory['foo'], portlet)
        self.assertEqual(self.factory['foo'].__parent__, self.factory)
        self.assertEqual(self.factory['foo'].__name__, 'foo')


class TestMailingFactory(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.acl import MailingFactory
        self.factory = MailingFactory(self.request)

    def tearDown(self):
        testing.tearDown()

    def test_init(self):
        self.assertIsNotNone(self.factory)
        self.assertEqual(self.factory.request, self.request)

    @mock.patch('pyramid_bimt.acl.Mailing')
    def test_non_existing_mailing(self, Mailing):
        Mailing.by_id.return_value = None
        with self.assertRaises(KeyError):
            self.factory[0]

    @mock.patch('pyramid_bimt.acl.Mailing')
    def test_existing_mailing(self, Mailing):
        mailing = mock.Mock()
        Mailing.by_id.return_value = mailing
        self.assertEqual(self.factory['foo'], mailing)
        self.assertEqual(self.factory['foo'].__parent__, self.factory)
        self.assertEqual(self.factory['foo'].__name__, 'foo')


class TestAuditLogFactory(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.acl import AuditLogFactory
        self.factory = AuditLogFactory(self.request)

    def tearDown(self):
        testing.tearDown()

    def test_init(self):
        self.assertIsNotNone(self.factory)
        self.assertEqual(self.factory.request, self.request)

    @mock.patch('pyramid_bimt.acl.AuditLogEntry')
    def test_non_existing_auditlog_entry(self, AuditLogEntry):
        AuditLogEntry.by_id.return_value = None
        with self.assertRaises(KeyError):
            self.factory[0]

    @mock.patch('pyramid_bimt.acl.AuditLogEntry')
    def test_existing_auditlog_entry(self, AuditLogEntry):
        entry = mock.Mock()
        AuditLogEntry.by_id.return_value = entry
        self.assertEqual(self.factory['foo'], entry)
        self.assertEqual(self.factory['foo'].__parent__, self.factory)
        self.assertEqual(self.factory['foo'].__name__, 'foo')
