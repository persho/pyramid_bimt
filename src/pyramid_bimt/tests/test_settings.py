# -*- coding: utf-8 -*-
"""Tests for settings view."""

from pyramid import testing
from pyramid.threadlocal import get_current_request
from pyramid_basemodel import Session
from pyramid_bimt import configure
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB

import mock
import unittest


class TestSettingsView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(request=testing.DummyRequest())
        self.request = get_current_request()
        self.request.user = mock.Mock()

        from pyramid_layout.layout import LayoutManager

        self.request.layout_manager = LayoutManager('context', 'requestr')

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_settings_view(self):
        from pyramid_bimt.views import SettingsForm
        request = testing.DummyRequest()
        request.context = mock.Mock()
        resp = SettingsForm(request)
        self.assertEqual(resp.title, 'Settings')

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_settings_view_response(self, find_layout):
        from pyramid_bimt.views import SettingsForm

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        find_layout.return_value = mock.Mock(spec='current_page')

        settings_view = SettingsForm(self.request)
        self.assertEqual(type(settings_view), SettingsForm)
        resp = settings_view()
        self.assertEqual('Settings', resp['title'])

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_settings_view_save_success(self, find_layout):
        from pyramid_bimt.views import SettingsForm

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        self.request.user.email = 'one@bar.com'
        form_values = {
            'account_info': {'email': 'TWO@bar.com'},
        }
        settings_view = SettingsForm(self.request)
        settings_view.save_success(form_values)
        self.assertEqual(self.request.user.email, 'two@bar.com')
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your changes have been saved.'],
        )

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_settings_view_save_success_same_email(self, find_layout):
        from pyramid_bimt.views import SettingsForm

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        self.request.user.email = 'one@bar.com'
        form_values = {
            'account_info': {'email': 'one@bar.com'},
        }
        settings_view = SettingsForm(self.request)
        settings_view.save_success(form_values)
        self.assertEqual(self.request.user.email, 'one@bar.com')
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your changes have been saved.'],
        )

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_regenerate_api_key_success(self, find_layout):
        from pyramid_bimt.views import SettingsForm

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        req = get_current_request()
        req.user = mock.Mock()
        settings_view = SettingsForm(req)
        settings_view.regenerate_api_key_success(None)
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'API key re-generated.'],
        )


class TestGenerateAPIKeyOnUserCreation(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB(groups=True, users=True, auditlog_types=True)
        configure(self.config)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.generate')
    def test_api_key_set_on_user_creation(self, mocked_generate):
        mocked_generate.return_value = 'foo'

        from pyramid_bimt.events import UserCreated

        user = User(email='foo@bar.com')
        Session.add(user)

        request = testing.DummyRequest()
        request.registry.notify(UserCreated(request, user, u'foö'))

        self.assertEqual(user.get_property('api_key', default=u''), u'foo')

    def test_generate_api_key(self):
        from pyramid_bimt.views import generate_api_key
        import re

        api_key = generate_api_key()

        self.assertEqual(type(api_key), unicode)
        self.assertIsNotNone(re.match(r'(....)-(....)-(....)-(....)', api_key))


class TestSubscription(unittest.TestCase):

    def setUp(self):
        initTestingDB(groups=True, users=True)
        self.config = testing.setUp()
        self.request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            user=User.by_id(2),
        )
        from pyramid_bimt.views import SettingsForm
        self.view = SettingsForm(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_subscribe_to_newsletter_button_missing(self, find_layout):
        response = self.view()
        self.assertNotIn('Subscribe to newsletter', response['form'])

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_subscribe_to_newsletter_button_present(self, find_layout):
        self.request.user.unsubscribe()
        response = self.view()
        self.assertIn('Subscribe to newsletter', response['form'])

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_subscribe_to_newsletter_unsubscribed(self, find_layout):
        self.request.user.unsubscribe()
        self.view.subscribe_to_newsletter_success(None)
        self.assertEqual(
            self.request.session['_f_'],
            [u'You have been subscribed to newsletter.'],
        )
        self.assertFalse(self.request.user.unsubscribed)
