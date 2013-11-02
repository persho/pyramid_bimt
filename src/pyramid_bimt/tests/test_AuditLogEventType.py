# -*- coding: utf-8 -*-
"""Tests for AuditLogEventType."""

from pyramid import testing

import unittest


class TestAuditLogEventType(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_default_event_types(self):
        """Test that the list of default event types is built correctly."""
        from pyramid_bimt.scripts.populate import default_audit_log_event_types
        types = default_audit_log_event_types()

        self.assertEqual(types[0].name, 'UserChangedPassword')
        self.assertEqual(types[0].title, 'User Changed Password')
        self.assertEqual(types[0].description, 'Emitted whenever a user changes its password.')  # noqa

        self.assertEqual(types[1].name, 'UserDeleted')
        self.assertEqual(types[1].title, 'User Deleted')
        self.assertEqual(types[1].description, 'Emitted whenever a user is deleted.')  # noqa

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

        self.assertEqual(types[6].name, 'UserSignedUp')
        self.assertEqual(types[6].title, 'User Signed Up')
        self.assertEqual(types[6].description, 'Emitted whenever a new user is created.')  # noqa
