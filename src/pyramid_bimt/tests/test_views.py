# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt import configure

import unittest
import webtest


class TestUserView(unittest.TestCase):
    def setUp(self):
        testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_view_user(self):
        from pyramid_bimt.views import UserView
        from pyramid_bimt.models import User
        request = testing.DummyRequest()
        context = User.get("admin@bar.com")
        resp = UserView(context, request).view()
        self.assertEqual(resp["user"], context)
        self.assertEqual(resp["fields"], [{"key": "bnh", "value": "on"}])


class TestUserViewFunctional(unittest.TestCase):
    def setUp(self):
        class MyLayout(object):
            def __init__(self, context, request):
                self.request = request
                self.context = context

        self.config = testing.setUp()
        initTestingDB()
        configure(self.config)
        self.config.add_layout(
            MyLayout,
            'pyramid_bimt:templates/main.pt',
            name="default"
        )
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_view_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users/admin@bar.com', status=200)
        self.assertIn("admin@bar.com", resp.text)

    def test_view_users(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        resp = self.testapp.get('/users', status=200)
        self.assertIn("admin@bar.com", resp.text)

    def test_disable_enable_user(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        self.testapp.get('/users/admin@bar.com/disable', status=302)
        self.testapp.get('/users/admin@bar.com/enable', status=302)
