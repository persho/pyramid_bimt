# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt views."""

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid_basemodel import Session
from pyramid_bimt import add_home_view
from pyramid_bimt import configure
from pyramid_bimt.testing import initTestingDB

import colander
import mock
import unittest
import webtest


class TestLoginViewsFunctional(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
            'bimt.disabled_user_redirect_path': '/settings',
            'mail.default_sender': 'test_sender',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB(auditlog_types=True, groups=True, users=True)
        configure(self.config)
        add_home_view(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_login(self):
        resp = self.testapp.get('/login', status=200)
        self.assertIn('<h1>Login</h1>', resp.text)
        resp.form['email'] = 'ONE@bar.com'
        resp.form['password'] = 'secret'
        resp = resp.form.submit('login')
        self.assertIn('302 Found', resp.text)
        resp = resp.follow()
        self.assertIn('Login successful.', resp.text)

    def test_login_wrong_password(self):
        resp = self.testapp.get('/login', status=200)
        self.assertIn('<h1>Login</h1>', resp.text)
        resp.form['email'] = 'ONE@bar.com'
        resp.form['password'] = 'foo'
        resp = resp.form.submit('login')
        self.assertIn('Login failed.', resp.text)

    def test_login_disabled(self):
        from pyramid_bimt.models import User
        user = User.by_email('one@bar.com')
        user.disable()

        resp = self.testapp.get('/login', status=200)
        self.assertIn('<h1>Login</h1>', resp.text)

        resp.form['email'] = 'ONE@bar.com'
        resp.form['password'] = 'secret'
        resp = resp.form.submit('login')
        self.assertIn('302 Found', resp.text)
        # /settings path does not exist in this package,
        # therefore we check for 404
        with self.assertRaises(HTTPNotFound) as cm:
            resp.follow()
        if cm.exception.message != '/settings':  # pragma: no cover
            self.fail(
                'This test should fail with message /settings! '
                'But it fails with message {}'.format(cm.exception.message)
            )

    class _MessageMatcher(object):
        def __init__(self, compare, msg):
            self.msg = msg
            self.compare = compare

        def __eq__(self, other):
            return self.compare(self.msg, other)

    @mock.patch('pyramid_bimt.views.auth.get_mailer')
    def test_login_reset_password(self, get_mailer):
        resp = self.testapp.get('/login', status=200)
        from pyramid_mailer.message import Message
        self.assertIn('<h1>Login</h1>', resp.text)
        resp.form['email'] = 'ONE@bar.com'
        resp = resp.form.submit('reset_password')
        self.assertIn('302 Found', resp.text)
        resp = resp.follow()
        self.assertIn('A new password was sent to your email.', resp.text)
        message = Message(
            subject='{} Password Reset'.format('BIMT'),
            recipients=['one@bar.com', ],
            body='test',
        )
        match_message = self._MessageMatcher(compare_message, message)
        get_mailer().send.assert_called_with(match_message)

        with self.assertRaises(AssertionError):
            message.subject = 'test'
            match_message = self._MessageMatcher(compare_message, message)
            get_mailer().send.assert_called_with(match_message)

    def test_login_reset_password_no_user(self):
        resp = self.testapp.get('/login', status=200)
        self.assertIn('<h1>Login</h1>', resp.text)
        resp.form['email'] = 'foo@bar.com'
        resp = resp.form.submit('reset_password')
        self.assertIn('Password reset failed. Make sure you have correctly '
                      'entered your email address.', resp.text)


def compare_message(self, other):
    if (self.subject == other.subject and
            self.sender == other.sender and
            self.recipients == other.recipients):
        return True
    else:
        return False


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


class TestLogoutView(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB(auditlog_types=True, groups=True, users=True)
        configure(self.config)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_logout_view(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.views.auth import logout
        context = User.by_email('admin@bar.com')
        request = testing.DummyRequest(layout_manager=mock.Mock())
        request.user = context
        self.assertEqual(
            logout(context, request).location,
            request.params.get('came_from', request.application_url)
        )


class TestForbiddenRedirect(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        configure(self.config)

    def tearDown(self):
        testing.tearDown()

    def test_forbidden_redirect_view(self):
        from pyramid_bimt.views.auth import forbidden_redirect
        request = testing.DummyRequest(layout_manager=mock.Mock())
        self.assertEqual(
            forbidden_redirect(None, request).location,
            request.route_path('login', _query={'came_from': request.url}),
        )


class TestErrorViews(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        configure(self.config)

    def tearDown(self):
        testing.tearDown()

    def test_raise_js_error(self):
        from pyramid_bimt.views.misc import raise_js_error
        request = testing.DummyRequest()
        self.assertEqual(raise_js_error(request)['title'], 'JS error')

    def test_raise_http_error(self):
        from pyramid_bimt.views.misc import raise_http_error
        request = testing.DummyRequest()
        request.matchdict = {'error_code': 404}
        with self.assertRaises(HTTPNotFound):
            raise_http_error(request)


class TestConfig(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.misc.os')
    def test_environ(self, patched_os):
        from pyramid_bimt.views.misc import config
        request = testing.DummyRequest(layout_manager=mock.Mock())

        patched_os.environ = {'c': '3', 'a': '1', 'b': '2'}

        result = config(request)

        self.assertEqual(
            result['environ'], [('a', '1'), ('b', '2'), ('c', '3')]
        )

    def test_settings(self):
        from pyramid_bimt.views.misc import config
        request = testing.DummyRequest(layout_manager=mock.Mock())

        request.registry.settings = {'c': '3', 'a': '1', 'b': '2'}

        result = config(request)

        self.assertEqual(
            result['settings'], [('a', '1'), ('b', '2'), ('c', '3')]
        )


class TestFormView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        from pyramid_bimt.views import FormView
        self.view = FormView(self.request)

        self.view.title = 'Foo Form'
        self.view.schema = colander.MappingSchema()

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.app_assets')
    @mock.patch('pyramid_bimt.views.form_assets')
    def test_assets(self, form_assets, app_assets):
        self.view()
        app_assets.need.assert_called_with()
        form_assets.need.assert_called_with()

    def test_title(self):
        result = self.view()
        self.assertEqual(result['title'], 'Foo Form')

    def test_hide_sidebar(self):
        self.request.layout_manager = mock.Mock()
        self.view.hide_sidebar = True
        self.view()
        self.request.layout_manager.layout.hide_sidebar = True

    def test_description(self):
        self.view.description = 'See me maybe?'
        result = self.view()
        self.assertEqual(result['title'], 'Foo Form')
        self.assertEqual(result['description'], 'See me maybe?')

    def test_no_description(self):
        result = self.view()
        self.assertEqual(result['title'], 'Foo Form')
        self.assertEqual(result['description'], None)
