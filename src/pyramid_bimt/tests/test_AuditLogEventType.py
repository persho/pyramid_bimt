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

    def test_get_event_type_by_id(self):
        from pyramid_bimt.models import AuditLogEventType

        self.assertEqual(AuditLogEventType.by_id(1).name, 'UserChangedPassword')  # noqa
        self.assertEqual(AuditLogEventType.by_id(1).title, 'User Changed Password')  # noqa
        self.assertEqual(AuditLogEventType.by_id(1).description, 'Emitted whenever a user changes its password.')  # noqa

    def test_get_event_type_get_all(self):
        from pyramid_bimt.scripts.populate import default_audit_log_event_types
        from pyramid_bimt.models import AuditLogEventType
        event_types = default_audit_log_event_types()
        db_event_types = AuditLogEventType.get_all()
        self.assertEqual(event_types[0].name, db_event_types[0].name)
        self.assertEqual(db_event_types.count(), len(event_types))
        self.assertEqual(
            AuditLogEventType.get_all(filter_by={'name': 'UserLoggedOut'})[0].name,  # noqa
            'UserLoggedOut',
        )

    def test_get_event_type_by_name(self):
        from pyramid_bimt.models import AuditLogEventType

        self.assertEqual(AuditLogEventType.by_name('UserChangedPassword').id, 1)  # noqa
        self.assertEqual(AuditLogEventType.by_name('UserChangedPassword').title, 'User Changed Password')  # noqa
        self.assertEqual(AuditLogEventType.by_name('UserChangedPassword').description, 'Emitted whenever a user changes its password.')  # noqa
