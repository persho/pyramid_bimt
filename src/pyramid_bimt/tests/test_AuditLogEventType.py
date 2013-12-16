# -*- coding: utf-8 -*-
"""Tests for AuditLogEventType."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB

import unittest


class TestAuditLogEventType(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_default_event_types(self):
        """Test that the list of default event types is built correctly."""
        from pyramid_bimt.scripts.populate import default_audit_log_event_types
        types = default_audit_log_event_types()

        self.assertEqual(types[0].name, 'UserChangedPassword')
        self.assertEqual(types[0].title, 'User Changed Password')
        self.assertEqual(types[0].description, 'Emitted whenever a user changes its password.')  # noqa

        self.assertEqual(types[1].name, 'UserCreated')
        self.assertEqual(types[1].title, 'User Created')
        self.assertEqual(types[1].description, 'Emitted whenever a new user is created.')  # noqa

        self.assertEqual(types[2].name, 'UserDisabled')
        self.assertEqual(types[2].title, 'User Disabled')
        self.assertEqual(types[2].description, 'Emitted whenever a user is disabled.')  # noqa

        self.assertEqual(types[3].name, 'UserEnabled')
        self.assertEqual(types[3].title, 'User Enabled')
        self.assertEqual(types[3].description, 'Emitted whenever a user is enabled.')  # noqa

        self.assertEqual(types[4].name, 'UserLoggedIn')
        self.assertEqual(types[4].title, 'User Logged In')
        self.assertEqual(types[4].description, 'Emitted whenever a user logs in.')  # noqa

        self.assertEqual(types[5].name, 'UserLoggedOut')
        self.assertEqual(types[5].title, 'User Logged Out')
        self.assertEqual(types[5].description, 'Emitted whenever a user logs out.')  # noqa

    def test_event_types_search(self):
        """Test searching for event types"""
        from pyramid_bimt.scripts.populate import default_audit_log_event_types

        from pyramid_bimt.models import AuditLogEventType

        self.assertEqual(AuditLogEventType.by_id(1).name, 'UserChangedPassword')  # noqa
        self.assertEqual(AuditLogEventType.by_id(1).title, 'User Changed Password')  # noqa
        self.assertEqual(AuditLogEventType.by_id(1).description, 'Emitted whenever a user changes its password.')  # noqa

        self.assertEqual(AuditLogEventType.by_id(2).name, 'UserCreated')
        self.assertEqual(AuditLogEventType.by_id(2).title, 'User Created')
        self.assertEqual(AuditLogEventType.by_id(2).description, 'Emitted whenever a new user is created.')  # noqa

        self.assertEqual(AuditLogEventType.by_id(3).name, 'UserDisabled')
        self.assertEqual(AuditLogEventType.by_id(3).title, 'User Disabled')
        self.assertEqual(AuditLogEventType.by_id(3).description, 'Emitted whenever a user is disabled.')  # noqa

        self.assertEqual(AuditLogEventType.by_id(4).name, 'UserEnabled')
        self.assertEqual(AuditLogEventType.by_id(4).title, 'User Enabled')
        self.assertEqual(AuditLogEventType.by_id(4).description, 'Emitted whenever a user is enabled.')  # noqa

        self.assertEqual(AuditLogEventType.by_id(5).name, 'UserLoggedIn')
        self.assertEqual(AuditLogEventType.by_id(5).title, 'User Logged In')
        self.assertEqual(AuditLogEventType.by_id(5).description, 'Emitted whenever a user logs in.')  # noqa

        self.assertEqual(AuditLogEventType.by_id(6).name, 'UserLoggedOut')
        self.assertEqual(AuditLogEventType.by_id(6).title, 'User Logged Out')
        self.assertEqual(AuditLogEventType.by_id(6).description, 'Emitted whenever a user logs out.')  # noqa

        event_types = default_audit_log_event_types()

        db_event_types = AuditLogEventType.get_all()
        self.assertEqual(event_types[0].name, db_event_types[0].name)
        self.assertEqual(db_event_types.count(), len(event_types))

        self.assertEqual(
            AuditLogEventType.get_all(filter_by={'name': 'UserLoggedOut'})[0].name,  # noqa
            'UserLoggedOut',
        )
