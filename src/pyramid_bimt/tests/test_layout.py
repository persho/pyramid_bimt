# -*- coding: utf-8 -*-
"""Tests for the default layout."""

from pyramid import testing

import mock
import unittest


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
