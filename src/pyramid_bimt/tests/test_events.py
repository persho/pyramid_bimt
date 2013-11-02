# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt events."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB

import mock
import unittest


def _make_user():
    user = mock.Mock(spec='id'.split())
    user.id = 1
    return user


class TestUserSignedUpEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserSignedUp
        request = testing.DummyRequest()
        user = _make_user()
        event = UserSignedUp(request, user, data={'foo'})
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.data, {'foo'})

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserSignedUp
        from pyramid_bimt.models import AuditLogEntry
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserSignedUp(request, user))
        entries = list(AuditLogEntry.get_all())

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user_id, 1)
        self.assertEqual(entries[0].event_type_id, 5)


class TestUserLoggedInEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserLoggedIn
        request = testing.DummyRequest()
        user = _make_user()
        event = UserLoggedIn(request, user, data={'foo'})
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.data, {'foo'})

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserLoggedIn
        from pyramid_bimt.models import AuditLogEntry
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserLoggedIn(request, user))
        entries = list(AuditLogEntry.get_all())

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user_id, 1)
        self.assertEqual(entries[0].event_type_id, 3)


class TestUserLoggedOutEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserLoggedOut
        request = testing.DummyRequest()
        user = _make_user()
        event = UserLoggedOut(request, user, data={'foo'})
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.data, {'foo'})

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserLoggedOut
        from pyramid_bimt.models import AuditLogEntry
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserLoggedOut(request, user))
        entries = list(AuditLogEntry.get_all())

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user_id, 1)
        self.assertEqual(entries[0].event_type_id, 4)


class TestUserChangedPasswordEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserChangedPassword
        request = testing.DummyRequest()
        user = _make_user()
        event = UserChangedPassword(request, user, data={'foo'})
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.data, {'foo'})

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserChangedPassword
        from pyramid_bimt.models import AuditLogEntry
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserChangedPassword(request, user))
        entries = list(AuditLogEntry.get_all())

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user_id, 1)
        self.assertEqual(entries[0].event_type_id, 1)
