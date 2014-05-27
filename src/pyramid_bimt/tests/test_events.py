# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt events."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB

import unittest


def _make_user():
    user = User(email='foo@bar.com')
    Session.add(user)
    return user


class TestUserCreatedEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserCreated
        request = testing.DummyRequest()
        user = _make_user()
        event = UserCreated(request, user, u'test_password', comment=u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.password, u'test_password')
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserCreated
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(
            UserCreated(request, user, u'test_password', comment=u'foö')
        )
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserCreated')
        self.assertEqual(entries[0].comment, u'foö')


class TestUserLoggedInEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserLoggedIn
        request = testing.DummyRequest()
        user = _make_user()
        event = UserLoggedIn(request, user, u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserLoggedIn
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserLoggedIn(request, user, u'foö'))
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserLoggedIn')
        self.assertEqual(entries[0].comment, u'foö')


class TestUserLoggedInAsEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserLoggedInAs
        request = testing.DummyRequest()
        user = _make_user()
        event = UserLoggedInAs(request, user, u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserLoggedInAs
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserLoggedInAs(request, user, u'foö'))
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserLoggedInAs')
        self.assertEqual(entries[0].comment, u'foö')


class TestUserLoggedOutEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserLoggedOut
        request = testing.DummyRequest()
        user = _make_user()
        event = UserLoggedOut(request, user, u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserLoggedOut
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserLoggedOut(request, user, u'foö'))
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserLoggedOut')
        self.assertEqual(entries[0].comment, u'foö')


class TestUserChangedPasswordEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserChangedPassword
        request = testing.DummyRequest()
        user = _make_user()
        password = u'test_password'
        event = UserChangedPassword(request, user, password, comment=u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.password, password)
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserChangedPassword
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(
            UserChangedPassword(request, user, u'test_password', comment=u'foö')  # noqa
        )
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserChangedPassword')
        self.assertEqual(entries[0].comment, u'foö')


class TestUserDisabledEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserDisabled
        request = testing.DummyRequest()
        user = _make_user()
        event = UserDisabled(request, user, u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserDisabled
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserDisabled(request, user, u'foö'))
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserDisabled')
        self.assertEqual(entries[0].comment, u'foö')


class TestUserEnabledEvent(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test___init__(self):
        """Test the __init__ method."""
        from pyramid_bimt.events import UserEnabled
        request = testing.DummyRequest()
        user = _make_user()
        event = UserEnabled(request, user, u'foö')
        self.assertEqual(event.request, request)
        self.assertEqual(event.user, user)
        self.assertEqual(event.comment, u'foö')

    def test_logged_to_audit_log(self):
        """Test that the event is logged to the Audit log."""
        from pyramid_bimt.events import UserEnabled
        request = testing.DummyRequest()
        user = _make_user()

        request.registry.notify(UserEnabled(request, user, u'foö'))
        entries = user.audit_log_entries

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'foo@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserEnabled')
        self.assertEqual(entries[0].comment, u'foö')
