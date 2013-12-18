# -*- coding: utf-8 -*-
"""Tests for utils"""

from pyramid import testing

import unittest


class TestUtils(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_safe_eval(self):
        from pyramid_bimt.utils import safe_eval

        self.assertEqual(safe_eval('False'), False)
        self.assertEqual(safe_eval('True'), True)
        self.assertEqual(safe_eval('false'), False)
        self.assertEqual(safe_eval('true'), True)
        self.assertEqual(safe_eval('1337'), 1337)
        self.assertEqual(safe_eval('1337.1337'), 1337.1337)
        self.assertEqual(safe_eval('asdfghjkl'), 'asdfghjkl')
        self.assertEqual(safe_eval('asdfg hjkl'), 'asdfg hjkl')
        self.assertEqual(safe_eval('\'asdfg hjkl\''), 'asdfg hjkl')
        self.assertEqual(safe_eval('u\'true\''), u'true')
        self.assertEqual(
            safe_eval('raise Exception(\'Chrashed yet?\')'),
            'raise Exception(\'Chrashed yet?\')'
        )
        self.assertEqual(safe_eval('exit'), 'exit')
        self.assertEqual(safe_eval('exit(12)'), 'exit(12)')
        self.assertEqual(safe_eval('None'), None)

    def test_expandvars_dict(self,):
        from pyramid_bimt.utils import expandvars_dict
        settings = {
            'test_boolean': 'true',
            'test_integer': '1337',
            'test_string': '\'asdfg hjkl\'',
            'test_none': 'None',
        }

        expanded_settings = {
            'test_boolean': True,
            'test_integer': 1337,
            'test_string': 'asdfg hjkl',
            'test_none': None,
        }

        self.assertEqual(expanded_settings, expandvars_dict(settings))
