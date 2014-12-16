# -*- coding: utf-8 -*-
"""Tests for models mixins."""

from pyramid import testing
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from pyramid_bimt.models import GetByIdMixin
from pyramid_bimt.models import GetByNameMixin
from pyramid_bimt.testing import initTestingDB
from sqlalchemy import Column
from sqlalchemy import String

import unittest


class _TestModelId(Base, BaseMixin, GetByIdMixin):
    """A class representing a test model with GetByIdMixin mixin."""

    __tablename__ = 'test_id_models'


class _TestModelName(Base, BaseMixin, GetByNameMixin):
    """A class representing a test model with GetByNameMixin."""

    __tablename__ = 'test_name_models'

    name = Column(
        String,
        unique=True,
        nullable=False,
    )


class TestGetById(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id_with_default(self):
        self.assertEqual(_TestModelId.by_id(1, None), None)
        self.assertEqual(_TestModelId.by_id('foo', None), None)
        self.assertEqual(_TestModelId.by_id(None, None), None)

    def test_invalid_id_without_default(self):
        self.assertEqual(_TestModelId.by_id(1, None), None)
        with self.assertRaises(ValueError):
            _TestModelId.by_id('foo')
        with self.assertRaises(TypeError):
            _TestModelId.by_id(None)

    def test_valid_id(self):
        Session.add(_TestModelId(id=2))
        test_model = _TestModelId.by_id(2)
        self.assertEqual(test_model.id, 2)


class TestGetByName(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id(self):
        self.assertEqual(_TestModelName.by_name(1, None), None)
        self.assertEqual(_TestModelName.by_name('foo', None), None)
        self.assertEqual(_TestModelName.by_name('főő', None), None)
        self.assertEqual(_TestModelName.by_name(None, None), None)

    def test_invalid_id_without_default(self):
        self.assertEqual(_TestModelName.by_name(1), None)
        self.assertEqual(_TestModelName.by_name('foo'), None)
        self.assertEqual(_TestModelName.by_name(None), None)
        with self.assertRaises(UnicodeDecodeError):
            _TestModelName.by_name('főő')

    def test_valid_id(self):
        Session.add(_TestModelName(name='foo'))
        test_model = _TestModelName.by_name('foo')
        self.assertEqual(test_model.name, 'foo')
