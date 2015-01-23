# -*- coding: utf-8 -*-
"""Misc and tools tests."""

from pyramid import testing
from pyramid_bimt.const import Modes

import mock
import unittest


class TestCheckSettings(unittest.TestCase):

    def setUp(self):
        self.settings_full = {
            'bimt.mode': Modes.development.name,
            'session.key': 'bimt',
            'session.secret': 'secret',
            'session.encrypt_key': 'secret',
            'session.validate_key': 'secret',
            'session.type': 'cookie',
            'authtkt.secret': 'secret',
            'bimt.app_name': 'bimt',
            'bimt.app_secret': '',
            'bimt.app_title': 'BIMT',
            'bimt.disabled_user_redirect_path': '',
            'bimt.encryption_aes_16b_key': '',
            'mail.info_address': '',
            'script_location': '',
            'session.secret': '',
            'sqlalchemy.url': '',
        }
        self.config_full = testing.setUp(settings=self.settings_full)

        self.settings_full_production = self.settings_full.copy()
        self.settings_full_production.update({
            'bimt.jvzoo_secret_key': '',
            'bimt.clickbank_secret_key': '',
            'bimt.piwik_site_id': '',
            'bimt.amqp_username': '',
            'bimt.amqp_password': '',
            'bimt.amqp_apiurl': '',
            'bimt.kill_cloudamqp_connections': True,
            'bimt.products_to_ignore': '',
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
        except KeyError as ke:  # pragma: no cover
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

        self.config_full_production.registry.settings['bimt.mode'] = \
            Modes.production.name

        try:
            check_required_settings(self.config_full_production)
        except KeyError as ke:  # pragma: no cover
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

        self.config_full.registry.settings['bimt.mode'] = \
            Modes.production.name

        with self.assertRaises(KeyError) as cm:
            check_required_settings(self.config_full)

        self.assertIn('bimt.jvzoo_secret_key', cm.exception.message)


class TestAutoKillConnections(unittest.TestCase):

    def setUp(self):
        from pyramid_bimt import kill_connections
        self.kill_connections = kill_connections
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_no_exception(self):
        try:
            # empty arguments could throw exception
            self.kill_connections(username=None, password=None, apiurl=None)
        except:
            self.fail('kill_connections function should not raise exception')

    @mock.patch('pyramid_bimt.requests')
    def test_kill_connections(self, requests):
        requests.get.return_value.status_code = 200
        requests.get.return_value.json.return_value = [{'name': 'foo bar'}]

        self.kill_connections(
            username='foo', password='bar', apiurl='http://foo.bar')

        requests.delete.assert_called_with(
            'http://foo.bar/api/connections/foo%20bar',
            headers={'X-Reason': 'Auto-kill on app start'},
            auth=('foo', 'bar')
        )


class RoutesTrailingSlashTest(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        from pyramid_bimt import configure
        configure(self.config)

    def test_trailing_slash(self):
        routes = self.config.get_routes_mapper().routelist
        for route in routes:
            if route.name != '__deform_static/':
                self.assertEqual(route.path[-1], '/')
