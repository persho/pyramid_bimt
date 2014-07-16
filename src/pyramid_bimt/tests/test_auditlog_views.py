# -*- coding: utf-8 -*-
"""Tests for AuditLog views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt import configure
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB

import mock
import unittest
import webtest


class TestAuditLogView(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB(
            auditlog_types=True,
            auditlog_entries=True,
            groups=True,
            users=True,
        )
        configure(self.config)
        self.request = testing.DummyRequest(
            user=mock.Mock())
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_audit_log(self):
        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        resp = self.testapp.get('/activity', status=200)
        self.assertIn('<h1>Recent Activity</h1>', resp.text)

    def test_audit_log_delete(self):
        from pyramid_bimt.models import AuditLogEventType
        from pyramid_bimt.models import AuditLogEntry
        from pyramid_bimt.views.auditlog import audit_log_delete
        import transaction
        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        request = self.request
        entry = AuditLogEntry(
            user_id=1,
            event_type_id=AuditLogEventType.by_name('UserCreated').id,
        )
        Session.add(entry)
        request.context = entry
        transaction.commit()
        resp = audit_log_delete(request)
        self.assertIn('/activity', resp.location)

    def test_audit_log_add(self):
        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        resp = self.testapp.get('/audit-log/add', status=200)
        self.assertIn('<h1>Add Audit log entry</h1>', resp.text)

    def test_audit_log_add_submit_success(self):
        from pyramid_bimt.views.auditlog import AuditLogAddEntryForm
        import datetime
        audit_log_add_view = AuditLogAddEntryForm(self.request)
        form_values = {
            'timestamp': datetime.datetime.now(),
            'user_id': 1,
            'event_type_id': 1,
            'comment': 'testing',
            'read': True,
        }
        resp = audit_log_add_view.submit_success(form_values)
        self.assertIn('/activity', resp.location)

    def _make_view(self):
        from pyramid_bimt.views.auditlog import AuditLogAJAX

        view = AuditLogAJAX(self.request)
        view.populate_columns(AuditLogEntry.by_id(2))
        return view

    def test_populate_columns_admin(self):
        self.request.user.admin = True
        view = self._make_view()
        self.assertEqual(view.columns['comment'], u'unread entry')
        self.assertEqual(
            view.columns['event_type_id'], 'User Changed Password')
        self.assertEqual(
            view.columns['user_id'], '<a href="/user/3">one@bar.com</a>')
        self.assertEqual(
            view.columns['action'],
            """
            <a class="btn btn-xs btn-danger" href="/audit-log/2/delete">
              <span class="glyphicon glyphicon-remove-sign"></span> Delete
            </a>
            """,
        )

    def test_populate_columns_user(self):
        self.request.user.admin = False
        view = self._make_view()
        self.assertEqual(view.columns['comment'], u'unread entry')
        self.assertEqual(
            view.columns['event_type_id'], 'User Changed Password')
        self.assertEqual(
            view.columns['user_id'], '<a href="/user/3">one@bar.com</a>')
        self.assertEqual(view.columns['action'], None)

    def test_admin_mark_only_own_entries_as_unread(self):
        self.request.user = User.by_email('admin@bar.com')

        AuditLogEntry.by_id(2).user = User.by_email('admin@bar.com')
        AuditLogEntry.by_id(2).read = False
        self._make_view()
        self.assertEqual(AuditLogEntry.by_id(2).read, True)

        AuditLogEntry.by_id(2).user = User.by_email('one@bar.com')
        AuditLogEntry.by_id(2).read = False
        self._make_view()
        self.assertEqual(AuditLogEntry.by_id(2).read, False)
