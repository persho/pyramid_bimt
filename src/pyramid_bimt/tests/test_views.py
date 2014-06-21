# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt views."""

from collections import OrderedDict
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid_basemodel import Session
from pyramid_bimt import add_home_view
from pyramid_bimt import configure
from pyramid_bimt.testing import initTestingDB
from pyramid_mailer import get_mailer

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
        initTestingDB(
            auditlog_types=True,
            groups=True,
            users=True,
            mailings=True
        )
        configure(self.config)
        self.request = testing.DummyRequest()
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

    def test_login_reset_password(self):
        self.config.include('pyramid_mailer.testing')
        self.mailer = get_mailer(self.testapp.app.registry)
        resp = self.testapp.get('/login', status=200)
        self.assertIn('<h1>Login</h1>', resp.text)
        resp.form['email'] = 'ONE@bar.com'
        resp = resp.form.submit('reset_password')
        self.assertIn('302 Found', resp.text)
        resp = resp.follow()
        self.assertIn('A new password was sent to your email.', resp.text)
        self.assertEqual(self.mailer.outbox[0].subject, u'BIMT Password Reset')
        self.assertIn(u'Öne Bar', self.mailer.outbox[0].html)

    def test_login_reset_password_no_user(self):
        resp = self.testapp.get('/login', status=200)
        self.assertIn('<h1>Login</h1>', resp.text)
        resp.form['email'] = 'foo@bar.com'
        resp = resp.form.submit('reset_password')
        self.assertIn('Password reset failed. Make sure you have correctly '
                      'entered your email address.', resp.text)


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


class TestDatatablesAJAXView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest(user=mock.Mock())

        from pyramid_bimt.views import DatatablesDataView
        self.view = DatatablesDataView(self.request)

        self.view.model = mock.Mock()
        self.view.columns = OrderedDict()
        self.view.columns['foo'] = None
        self.view.columns['bar'] = None

    def tearDown(self):
        testing.tearDown()

    def test_sEcho(self):
        self.view.model.get_all.return_value.all.return_value = []
        self.request.GET['sEcho'] = '1'

        result = self.view()
        self.assertEqual(result['sEcho'], 1)

    def test_iTotalRecords_iTotalDisplayrecords(self):
        self.view.model.get_all.return_value.all.return_value = []
        self.view.model.get_all.return_value.count.return_value = 1

        result = self.view()
        self.assertEqual(result['iTotalRecords'], 1)
        self.assertEqual(result['iTotalDisplayRecords'], 1)

    def test_default_query_parameters(self):
        self.view.model.get_all.return_value.all.return_value = []
        self.view()

        self.view.model.get_all.assert_any_call(
            filter_by=None,
            search=None,
            order_by='foo',
            order_direction='asc',
            offset=(0, 10),
            security=False,
        )

    def test_arbitrary_query_parameters(self):
        self.request.GET['iDisplayStart'] = '5'
        self.request.GET['iDisplayLength'] = '50'
        self.request.GET['sSearch'] = 'foo'
        self.request.GET['iSortCol_0'] = '1'
        self.request.GET['sSortDir_0'] = 'desc'

        self.view.model.get_all.return_value.all.return_value = []
        self.view()

        self.view.model.get_all.assert_any_call(
            filter_by=None,
            search='foo',
            order_by='bar',
            order_direction='desc',
            offset=(5, 55),
            security=False,
        )


class TestDatatablesAJAXViewIntegration(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest(user=mock.Mock())

        from pyramid_bimt.views import DatatablesDataView
        from pyramid_bimt.models import AuditLogEntry

        self.view = DatatablesDataView(self.request)
        initTestingDB(auditlog_types=True)

        self.view.model = mock.Mock()
        self.view.columns = OrderedDict()
        self.view.columns['foo'] = None
        self.view.columns['bar'] = None

        Session.add(AuditLogEntry(comment=u'föo'))
        Session.add(AuditLogEntry(comment=u'bär'))
        Session.flush()

        class DummyDatatablesAJAXView(DatatablesDataView):

            model = AuditLogEntry

            columns = OrderedDict()
            columns['id'] = None
            columns['comment'] = None

            def populate_columns(self, entry):
                self.columns['id'] = entry.id
                self.columns['comment'] = entry.comment
                self.columns['DT_RowClass'] = 'info'

        self.datatable_view = DummyDatatablesAJAXView

    def tearDown(self):
        testing.tearDown()
        Session.remove()

    def test_integration(self):

        self.request.GET['sSearch'] = u'föo'

        resp = self.datatable_view(self.request)()
        self.assertEqual(resp['sEcho'], 0)
        self.assertEqual(resp['iTotalRecords'], 2)
        self.assertEqual(resp['iTotalDisplayRecords'], 1)
        self.assertEqual(
            resp['aaData'],
            [
                {0: 1, 1: u'föo', 'DT_RowClass': 'info'},
            ])

    def test_integration_filter_by_id(self):

        self.request.GET['filter_by.name'] = 'id'
        self.request.GET['filter_by.value'] = 1

        resp = self.datatable_view(self.request)()
        self.assertEqual(resp['sEcho'], 0)
        self.assertEqual(resp['iTotalRecords'], 2)
        self.assertEqual(resp['iTotalDisplayRecords'], 1)
        self.assertEqual(
            resp['aaData'],
            [
                {0: 1, 1: u'föo', 'DT_RowClass': 'info'},
            ],
        )

    def test_integration_filter_by_comment(self):

        self.request.GET['filter_by.name'] = 'comment'
        self.request.GET['filter_by.value'] = u'föo'

        resp = self.datatable_view(self.request)()
        self.assertEqual(resp['sEcho'], 0)
        self.assertEqual(resp['iTotalRecords'], 2)
        self.assertEqual(resp['iTotalDisplayRecords'], 1)
        self.assertEqual(
            resp['aaData'],
            [
                {0: 1, 1: u'föo', 'DT_RowClass': 'info'},
            ],
        )


class TestLoginAsView(unittest.TestCase):
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

    def test_loginas_view(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.views.auth import LoginAs
        context = User.by_email('admin@bar.com')
        request = testing.DummyRequest(layout_manager=mock.Mock())
        request.user = context
        resp = LoginAs(request)()
        self.assertEqual(resp['title'], 'Login as user')
        self.assertIn('Login as user', resp['form'])

    def test_loginas_view_submit_admin(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.views.auth import LoginAs
        context = User.by_email('admin@bar.com')
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            session=mock.Mock(),
        )
        form_values = {
            'email': 'one@bar.com'
        }
        request.user = context
        view = LoginAs(request)
        resp = view.login_as_success(form_values)
        self.assertEqual(resp.location, 'http://example.com')
        request.session.flash.assert_called_once_with(
            u'You have successfully logged in as user: one@bar.com'
        )

    def test_loginas_view_submit_admin_no_user(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.views.auth import LoginAs
        context = User.by_email('admin@bar.com')
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            session=mock.Mock(),
        )
        form_values = {
            'email': 'foo@bar.com'
        }
        request.user = context
        view = LoginAs(request)
        self.assertIsNone(view.login_as_success(form_values))
        request.session.flash.assert_called_once_with(
            u'User with that email does not exist.',
            'error'
        )

    def test_loginas_view_submit_admin_disabled_user(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.views.auth import LoginAs
        context = User.by_email('admin@bar.com')
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            session=mock.Mock(),
        )
        form_values = {
            'email': 'one@bar.com'
        }
        request.user = context
        view = LoginAs(request)
        User.by_email('one@bar.com').disable()
        self.assertIsNone(view.login_as_success(form_values))
        request.session.flash.assert_called_once_with(
            u'User: one@bar.com is disabled.',
            'warning'
        )

    def test_loginas_view_submit_staff_as_admin(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.models import Group
        from pyramid_bimt.views.auth import LoginAs
        context = User.by_email('one@bar.com')
        context.groups.append(Group.by_name('staff'))
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            session=mock.Mock(),
        )
        form_values = {
            'email': 'admin@bar.com'
        }
        request.user = context
        view = LoginAs(request)
        self.assertIsNone(view.login_as_success(form_values))
        request.session.flash.assert_called_once_with(
            u'You do not have permission to login as admin user.',
            'error'
        )
