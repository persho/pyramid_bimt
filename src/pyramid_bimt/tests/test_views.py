# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt views."""

from mock import patch
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid_basemodel import Session
from pyramid_bimt import add_home_view
from pyramid_bimt import configure
from pyramid_bimt.testing import initTestingDB

import unittest
import webtest


class TestLoginViewsFunctional(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB()
        configure(self.config)
        add_home_view(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_login(self):
        resp = self.testapp.get('/login', status=200)
        self.assertIn("<h1>Login</h1>", resp.text)
        resp.form['email'] = 'admin@bar.com'
        resp.form['password'] = 'secret'
        resp = resp.form.submit('login')
        self.assertIn("302 Found", resp.text)
        resp = resp.follow()
        self.assertIn("Login successful.", resp.text)


class TestUserView(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_view_user(self):
        from pyramid_bimt.views.user import UserView
        from pyramid_bimt.models import User
        context = User.by_email("admin@bar.com")
        request = testing.DummyRequest()
        resp = UserView(context, request).view()
        self.assertEqual(resp["user"], context)
        self.assertEqual(list(resp["audit_log_entries"]), [])
        self.assertEqual(resp["properties"], [{"key": "bimt", "value": "on"}])


class TestUserViewFunctional(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB()
        configure(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_view_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users/1', status=200)
        self.assertIn("admin@bar.com", resp.text)

    def test_view_users(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users', status=200)
        self.assertIn("admin@bar.com", resp.text)

    def test_disable_enable_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        self.testapp.get('/users/1/disable', status=302)
        self.testapp.get('/users/1/enable', status=302)

    def test_user_actions(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users', status=200)

        self.assertIn('href="http://localhost/users/1"', resp.text)
        self.assertIn('href="http://localhost/users/1/edit"', resp.text)
        self.assertIn('href="http://localhost/users/add"', resp.text)


class TestEditUserViewFunctional(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB()
        configure(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_add_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users/add', status=200)
        self.assertIn("<h1>Add User</h1>", resp.text)

    def test_edit_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users/1/edit', status=200)
        self.assertIn("<h1>Edit User</h1>", resp.text)

    def test_edit_no_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        self.assertRaises(
            HTTPNotFound, self.testapp.get, '/users/123456789/edit')


class TestConfig(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @patch("pyramid_bimt.views.misc.os")
    def test_environ(self, patched_os):
        from pyramid_bimt.views.misc import config
        request = testing.DummyRequest()

        patched_os.environ = {'c': '3', 'a': '1', 'b': '2'}

        result = config(request)

        self.assertEqual(
            result['environ'], [('a', '1'), ('b', '2'), ('c', '3')]
        )

    def test_settings(self):
        from pyramid_bimt.views.misc import config
        request = testing.DummyRequest()

        request.registry.settings = {'c': '3', 'a': '1', 'b': '2'}

        result = config(request)

        self.assertEqual(
            result['settings'], [('a', '1'), ('b', '2'), ('c', '3')]
        )
