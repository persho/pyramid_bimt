# -*- coding: utf-8 -*-
"""Tests for AuditLogEventType."""

from datetime import datetime
from datetime import timedelta
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.tests.test_user_model import _make_user

import unittest


def _make_entry(comment=u'', **kwargs):
    entry = AuditLogEntry(comment=comment, **kwargs)
    Session.add(entry)
    return entry


class TestAuditLogEventType(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test__repr__(self):
        self.assertEqual(
            repr(AuditLogEventType.by_id(1)),
            '<AuditLogEventType:1 (name=u\'SanityCheckDone\')>'
        )

    def test_default_event_types(self):
        """Test that the list of default event types is built correctly."""
        from pyramid_bimt.scripts.populate import default_audit_log_event_types
        types = default_audit_log_event_types()

        self.assertEqual(types[0].name, 'SanityCheckDone')
        self.assertEqual(types[0].title, 'Sanity Check Done')
        self.assertEqual(types[0].description, 'Emitted whenever a sanity check is done.')  # noqa

        self.assertEqual(types[1].name, 'UserChangedPassword')
        self.assertEqual(types[1].title, 'User Changed Password')
        self.assertEqual(types[1].description, 'Emitted whenever a user changes its password.')  # noqa

        self.assertEqual(types[2].name, 'UserCreated')
        self.assertEqual(types[2].title, 'User Created')
        self.assertEqual(types[2].description, 'Emitted whenever a new user is created.')  # noqa

        self.assertEqual(types[3].name, 'UserDisabled')
        self.assertEqual(types[3].title, 'User Disabled')
        self.assertEqual(types[3].description, 'Emitted whenever a user is disabled.')  # noqa

        self.assertEqual(types[4].name, 'UserEnabled')
        self.assertEqual(types[4].title, 'User Enabled')
        self.assertEqual(types[4].description, 'Emitted whenever a user is enabled.')  # noqa

        self.assertEqual(types[5].name, 'UserLoggedIn')
        self.assertEqual(types[5].title, 'User Logged In')
        self.assertEqual(types[5].description, 'Emitted whenever a user logs in.')  # noqa

        self.assertEqual(types[6].name, 'UserLoggedInAs')
        self.assertEqual(types[6].title, 'User Logged In As')
        self.assertEqual(types[6].description, 'Emitted whenever a user logs in as another user.')  # noqa

        self.assertEqual(types[7].name, 'UserLoggedOut')
        self.assertEqual(types[7].title, 'User Logged Out')
        self.assertEqual(types[7].description, 'Emitted whenever a user logs out.')  # noqa

    def test_get_event_type_by_id(self):
        from pyramid_bimt.models import AuditLogEventType

        self.assertEqual(AuditLogEventType.by_id(2).name, 'UserChangedPassword')  # noqa
        self.assertEqual(AuditLogEventType.by_id(2).title, 'User Changed Password')  # noqa
        self.assertEqual(AuditLogEventType.by_id(2).description, 'Emitted whenever a user changes its password.')  # noqa

    def test_get_event_type_get_all(self):
        from pyramid_bimt.scripts.populate import default_audit_log_event_types
        from pyramid_bimt.models import AuditLogEventType
        event_types = default_audit_log_event_types()
        db_event_types = AuditLogEventType.get_all()
        self.assertEqual(event_types[0].name, db_event_types[0].name)
        self.assertEqual(db_event_types.count(), len(event_types))
        self.assertEqual(
            AuditLogEventType.get_all(
                filter_by={'name': 'UserLoggedOut'})[0].name,
            'UserLoggedOut',
        )

    def test_get_event_type_by_name(self):
        from pyramid_bimt.models import AuditLogEventType

        self.assertEqual(AuditLogEventType.by_name('UserChangedPassword').id, 2)  # noqa
        self.assertEqual(AuditLogEventType.by_name('UserChangedPassword').title, 'User Changed Password')  # noqa
        self.assertEqual(AuditLogEventType.by_name('UserChangedPassword').description, 'Emitted whenever a user changes its password.')  # noqa

    def test_using_by_id_mixin(self):
        from pyramid_bimt.models import AuditLogEventType
        from pyramid_bimt.models import GetByIdMixin

        self.assertTrue(issubclass(AuditLogEventType, GetByIdMixin))

    def test_using_by_name_mixin(self):
        from pyramid_bimt.models import AuditLogEventType
        from pyramid_bimt.models import GetByNameMixin

        self.assertTrue(issubclass(AuditLogEventType, GetByNameMixin))


class TestAuditLogEntryModel(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB(auditlog_types=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_default_values(self):
        entry = _make_entry()
        Session.flush()
        self.assertAlmostEqual(
            entry.timestamp, datetime.utcnow(), delta=timedelta(seconds=10))

    def test__repr__(self):
        entry = _make_entry(
            id=1,
            user=_make_user(email='foo@bar.com'),
            event_type=AuditLogEventType.by_id(1),
        )
        self.assertEqual(
            repr(entry),
            '<AuditLogEntry:1 (user=\'foo@bar.com\', type=u\'SanityCheckDone\')>'  # noqa
        )

    def test__repr__empty_values(self):
        entry = _make_entry()
        self.assertEqual(
            repr(entry),
            '<AuditLogEntry:None (user=None, type=None)>'  # noqa
        )

    def test_using_by_id_mixin(self):
        from pyramid_bimt.models import AuditLogEntry
        from pyramid_bimt.models import GetByIdMixin

        self.assertTrue(issubclass(AuditLogEntry, GetByIdMixin))


class TestEntryGetAll(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

        # for these tests, disable security
        def get_all_new(class_, **kwargs):
            if kwargs.get('security') is None:  # pragma: no cover
                kwargs['security'] = False
            return AuditLogEntry.get_all_orig(**kwargs)

        AuditLogEntry.get_all_orig = AuditLogEntry.get_all
        AuditLogEntry.get_all = classmethod(get_all_new)

    def tearDown(self):
        AuditLogEntry.get_all = AuditLogEntry.get_all_orig
        Session.remove()
        testing.tearDown()

    def test_no_entries(self):
        entries = AuditLogEntry.get_all().all()
        self.assertEqual(len(entries), 0)

    def test_all_entries(self):
        _make_entry()
        _make_entry()
        _make_entry()
        entries = AuditLogEntry.get_all().all()
        self.assertEqual(len(entries), 3)

    def test_ordered_by_timestamp_by_default(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        _make_entry(comment=u'baz')
        entries = AuditLogEntry.get_all().all()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].comment, 'baz')
        self.assertEqual(entries[1].comment, 'bar')
        self.assertEqual(entries[2].comment, 'foo')

    def test_override_order_direction(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        _make_entry(comment=u'baz')
        entries = AuditLogEntry.get_all(order_direction='asc').all()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].comment, 'foo')
        self.assertEqual(entries[1].comment, 'bar')
        self.assertEqual(entries[2].comment, 'baz')

    def test_override_order_by(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        _make_entry(comment=u'baz')
        entries = AuditLogEntry.get_all(order_by='comment').all()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].comment, 'foo')
        self.assertEqual(entries[1].comment, 'baz')
        self.assertEqual(entries[2].comment, 'bar')

    def test_offset(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        _make_entry(comment=u'baz')
        entries = AuditLogEntry.get_all(offset=(1, 2)).all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].comment, 'bar')

    def test_search(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        _make_entry(comment=u'baz')
        entries = AuditLogEntry.get_all(search='ba').all()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].comment, 'baz')
        self.assertEqual(entries[1].comment, 'bar')

    def test_filter_by(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        entries = AuditLogEntry.get_all(filter_by={'comment': u'foo'}).all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].comment, 'foo')

    def test_limit(self):
        _make_entry(comment=u'foo')
        _make_entry(comment=u'bar')
        entries = AuditLogEntry.get_all(limit=1).all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].comment, 'bar')

    def test_security_no_request(self):
        with self.assertRaises(KeyError) as cm:
            AuditLogEntry.get_all(security=True)
        self.assertEqual(
            cm.exception.message,
            'You must provide request when security is True!'
        )
