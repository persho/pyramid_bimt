# -*- coding: utf-8 -*-
"""Misc and tools tests."""

from pyramid import testing

import mock
import unittest


class TestCheckSettings(unittest.TestCase):

    def setUp(self):
        self.settings_full = {
            'authtkt.secret': '',
            'bimt.app_name': 'bimt',
            'bimt.app_title': 'BIMT',
            'script_location': '',
            'session.secret': '',
            'sqlalchemy.url': '',
        }
        self.config_full = testing.setUp(settings=self.settings_full)

        self.settings_full_production = self.settings_full.copy()
        self.settings_full_production.update({
            'bimt.jvzoo_regular_period': '',
            'bimt.jvzoo_secret_key': '',
            'bimt.jvzoo_trial_period': '',
            'bimt.piwik_site_id': '',
            'mail.default_sender': 'test@xyz.xyz',
            'mail.host': '',
            'mail.password': '',
            'mail.port': '',
            'mail.tls': '',
            'mail.username': '',
        })
        self.config_full_production = testing.setUp(
            settings=self.settings_full_production)

        self.config_empty = testing.setUp(settings={})

        self.settings_missing = self.settings_full.copy()
        del self.settings_missing['bimt.app_name']
        self.config_missing = testing.setUp(settings=self.settings_missing)

    def tearDown(self):
        testing.tearDown()

    def test_check_required_settings(self):
        from pyramid_bimt import check_required_settings

        try:
            check_required_settings(self.config_full)
        except KeyError as ke:
            self.fail(ke.message)

    def test_empty_required_settings(self):
        from pyramid_bimt import check_required_settings
        with self.assertRaises(KeyError):
            check_required_settings(self.config_empty)

    def test_missing_required_settings(self):
        from pyramid_bimt import check_required_settings

        with self.assertRaises(KeyError) as cm:
            check_required_settings(self.config_missing)

        self.assertIn('bimt.app_name', cm.exception.message)

    @mock.patch('pyramid_bimt.sys')
    def test_check_required_settings_production(self, patched_sys):
        from pyramid_bimt import check_required_settings

        patched_sys.argv = ['pserve', 'production.ini']

        try:
            check_required_settings(self.config_full_production)
        except KeyError as ke:
            self.fail(ke.message)

    @mock.patch('pyramid_bimt.sys')
    def test_empty_required_settings_production(self, patched_sys):
        from pyramid_bimt import check_required_settings
        patched_sys.argv = ['pserve', 'production.ini']
        with self.assertRaises(KeyError):
            check_required_settings(self.config_empty)

    @mock.patch('pyramid_bimt.sys')
    def test_missing_required_settings_production(self, patched_sys):
        from pyramid_bimt import check_required_settings

        patched_sys.argv = ['pserve', 'production.ini']

        with self.assertRaises(KeyError) as cm:
            check_required_settings(self.config_missing)

        self.assertIn('bimt.app_name', cm.exception.message)
