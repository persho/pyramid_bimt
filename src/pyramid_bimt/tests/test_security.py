# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt events."""

from pyramid import testing

import unittest

from zope.testing.loggingsupport import InstalledHandler
handler = InstalledHandler('pyramid_bimt.security')


class TestVerify(unittest.TestCase):

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_invalid_cyphertext(self):
        """Test handling of an invalid cyphertext stored in DB."""
        from pyramid_bimt.security import verify
        self.assertFalse(verify('foo', 'invalid'))

        # error is not raised, but it is written to log so we get notified
        self.assertEqual(len(handler.records), 1)
        self.assertEqual(
            handler.records[0].message, 'hash could not be identified')

    def test_verify(self):
        from pyramid_bimt.security import generate
        from pyramid_bimt.security import encrypt
        from pyramid_bimt.security import verify

        generated_pass = generate()
        encrypted_pass = encrypt(generated_pass)

        self.assertTrue(verify(generated_pass, encrypted_pass))

    def test_verify_none(self):
        from pyramid_bimt.security import generate
        from pyramid_bimt.security import encrypt
        from pyramid_bimt.security import verify

        generated_pass = generate()
        encrypted_pass = encrypt(generated_pass)

        self.assertFalse(verify(None, encrypted_pass))

    def test_verify_wrong_type(self):
        from pyramid_bimt.security import generate
        from pyramid_bimt.security import encrypt
        from pyramid_bimt.security import verify

        generated_pass = generate()
        encrypted_pass = encrypt(generated_pass)

        self.assertFalse(verify(object(), encrypted_pass))
