# -*- coding: utf-8 -*-
"""Tests for the ACL."""

from pyramid import testing
from pyramid.httpexceptions import HTTPFound

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

    def test_redirect_to_nonslash(self):
        from pyramid_bimt import add_routes_user
        add_routes_user(self.config)
        self.request['PATH_INFO'] = '/users/'
        with self.assertRaises(HTTPFound) as cm:
            from pyramid_bimt.acl import UserFactory
            UserFactory(self.request)
        self.assertEqual(cm.exception.location, '/users')


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

    def test_redirect_to_nonslash(self):
        from pyramid_bimt import add_routes_group
        add_routes_group(self.config)
        self.request['PATH_INFO'] = '/groups/'
        with self.assertRaises(HTTPFound) as cm:
            from pyramid_bimt.acl import GroupFactory
            GroupFactory(self.request)
        self.assertEqual(cm.exception.location, '/groups')


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

    def test_redirect_to_nonslash(self):
        from pyramid_bimt import add_routes_portlet
        add_routes_portlet(self.config)
        self.request['PATH_INFO'] = '/portlets/'
        with self.assertRaises(HTTPFound) as cm:
            from pyramid_bimt.acl import PortletFactory
            PortletFactory(self.request)
        self.assertEqual(cm.exception.location, '/portlets')


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

    def test_redirect_to_nonslash(self):
        from pyramid_bimt import add_routes_audit_log
        add_routes_audit_log(self.config)
        self.request['PATH_INFO'] = '/audit-log/'
        with self.assertRaises(HTTPFound) as cm:
            from pyramid_bimt.acl import AuditLogFactory
            AuditLogFactory(self.request)
        self.assertEqual(cm.exception.location, '/audit-log')
