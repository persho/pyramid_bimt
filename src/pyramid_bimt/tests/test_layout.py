# -*- coding: utf-8 -*-
"""Tests for the default layout."""

from pyramid import testing
from pyramid_bimt.layout import above_content_portlets
from pyramid_bimt.layout import above_footer_portlets
from pyramid_bimt.layout import below_sidebar_portlets
from pyramid_bimt.models import Portlet

import mock
import unittest


class TestPortletsFetchers(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.context = mock.Mock(specs=())

    def tearDown(self):
        testing.tearDown()

    def test_anonymous(self):
        request = testing.DummyRequest(user=None)

        self.assertEqual(above_content_portlets(self.context, request), '')
        self.assertEqual(below_sidebar_portlets(self.context, request), '')
        self.assertEqual(above_footer_portlets(self.context, request), '')

    @mock.patch('pyramid_bimt.layout.Portlet')
    def test_user_with_no_portlets(self, Portlet):
        request = testing.DummyRequest(user=mock.Mock(specs=()))
        Portlet.by_user_and_position.return_value = []

        self.assertEqual(above_content_portlets(self.context, request), '')
        self.assertEqual(below_sidebar_portlets(self.context, request), '')
        self.assertEqual(above_footer_portlets(self.context, request), '')

    @mock.patch('pyramid_bimt.layout.Portlet')
    def test_user_with_a_single_portlet(self, MockedPortlet):
        from pyramid_bimt.layout import above_content_portlets
        request = testing.DummyRequest(user=mock.Mock(specs=()))
        MockedPortlet.by_user_and_position.return_value = [
            Portlet(html=u'foö'), ]

        self.assertEqual(above_content_portlets(self.context, request), u'foö')
        self.assertEqual(below_sidebar_portlets(self.context, request), u'foö')
        self.assertEqual(above_footer_portlets(self.context, request), u'foö')

    @mock.patch('pyramid_bimt.layout.Portlet')
    def test_user_with_multiple_portlets(self, MockedPortlet):
        from pyramid_bimt.layout import above_content_portlets
        request = testing.DummyRequest(user=mock.Mock(specs=()))
        MockedPortlet.by_user_and_position.return_value = [
            Portlet(html=u'foö'), Portlet(html=u'bär')]

        self.assertEqual(above_content_portlets(self.context, request), u'foöbär')  # noqa
        self.assertEqual(below_sidebar_portlets(self.context, request), u'foöbär')  # noqa
        self.assertEqual(above_footer_portlets(self.context, request), u'foöbär')   # noqa


class TestFlashMessages(unittest.TestCase):

    def setUp(self):
        self.settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=self.settings)

        self.context = mock.Mock()
        self.request = testing.DummyRequest()

        from pyramid_bimt.layout import DefaultLayout
        self.layout = DefaultLayout(self.context, self.request)

    def tearDown(self):
        testing.tearDown()

    def test_no_messages(self):
        messages = self.layout.flash_messages()
        self.assertEqual(len(messages), 0)

    def test_info_message(self):
        self.request.session.flash('foo', 'info')
        messages = self.layout.flash_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], {'msg': 'foo', 'level': 'info'})

    def test_warning_message(self):
        self.request.session.flash('foo', 'warning')
        messages = self.layout.flash_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], {'msg': 'foo', 'level': 'warning'})

    def test_error_message(self):
        self.request.session.flash('foo', 'error')
        messages = self.layout.flash_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], {'msg': 'foo', 'level': 'danger'})

    def test_no_message_level(self):
        self.request.session.flash('foo')
        messages = self.layout.flash_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], {'msg': 'foo', 'level': 'info'})
