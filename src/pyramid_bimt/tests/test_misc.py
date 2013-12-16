# -*- coding: utf-8 -*-
"""Misc and tools tests."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB

import mock
import unittest


class TestCheckSettings(unittest.TestCase):

    def setUp(self):
        self.settings_full = {
            'authtkt.secret': '',
            'bimt.app_name': 'bimt',
            'bimt.app_title': 'BIMT',
            'bimt.disabled_user_redirect_path': '',
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

        patched_sys.argv = ['pserve', 'production.ini']

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

        patched_sys.argv = ['pserve', 'production.ini']

        with self.assertRaises(KeyError) as cm:
            check_required_settings(self.config_full)

        self.assertIn('bimt.jvzoo_regular_period', cm.exception.message)


class TestACL(unittest.TestCase):
    def setUp(self):
        from pyramid_bimt import configure
        self.config = testing.setUp()
        configure(self.config)
        self.request = testing.DummyRequest()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_groupfinder(self):
        from pyramid_bimt.acl import groupfinder
        self.assertEqual(
            groupfinder('one@bar.com', self.request),
            ['g:users'],
        )
        self.assertEqual(
            groupfinder('foo@bar.com', self.request),
            [],
        )

    def test_factories(self):
        from pyramid_bimt.acl import AuditLogFactory
        from pyramid_bimt.acl import RootFactory
        from pyramid_bimt.acl import UserFactory
        from pyramid_bimt.models import AuditLogEntry
        from pyramid.httpexceptions import HTTPFound
        import transaction

        entry = AuditLogEntry(
            user_id=1,
            event_type_id=1,
        )
        Session.add(entry)
        transaction.commit()
        audit_log_factory = AuditLogFactory(self.request)
        self.assertEqual(
            audit_log_factory[1].id,
            1,
        )
        with self.assertRaises(KeyError):
            audit_log_factory[0]

        self.assertIsNotNone(RootFactory(self.request))

        self.assertIsNotNone(UserFactory(self.request))

        with self.assertRaises(HTTPFound):
            self.request['PATH_INFO'] = '/users/'
            UserFactory(self.request)
