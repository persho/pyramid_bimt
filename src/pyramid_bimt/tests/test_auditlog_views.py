# -*- coding: utf-8 -*-
"""Tests for AuditLog views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt import configure
from pyramid_bimt.testing import initTestingDB

import unittest
import webtest


class TestAuditLogView(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB(auditlog_types=True, groups=True, users=True)
        configure(self.config)
        self.request = testing.DummyRequest()
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_audit_log(self):
        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        resp = self.testapp.get('/audit-log', status=200)
        self.assertIn('<h1>Audit Log</h1>', resp.text)

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
        self.assertIn('/audit-log', resp.location)

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
            'comment': 'testing'
        }
        resp = audit_log_add_view.submit_success(form_values)
        self.assertIn('/audit-log', resp.location)

    def test_populate_columns(self):
        from pyramid_bimt.models import AuditLogEntry
        from pyramid_bimt.views.auditlog import AuditLogAJAX

        Session.add(AuditLogEntry(comment=u'föo', event_type_id=1, user_id=1))
        Session.flush()

        view = AuditLogAJAX(self.request)
        AuditLogAJAX(self.request).populate_columns(AuditLogEntry.by_id(1))
        self.assertEqual(view.columns['comment'], u'föo')
        self.assertEqual(
            view.columns['event_type_id'], 'User Changed Password')
        self.assertEqual(
            view.columns['user_id'], '<a href="/user/1">admin@bar.com</a>')
        self.assertEqual(
            view.columns['action'],
            """
        <a class="btn btn-xs btn-danger" href="/audit-log/1/delete">
          <span class="glyphicon glyphicon-remove-sign"></span> Delete
        </a>
        """,
        )
