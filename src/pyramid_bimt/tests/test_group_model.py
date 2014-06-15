# -*- coding: utf-8 -*-
"""Tests for the Group model."""

from pyramid_bimt.models import Group
from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.testing import initTestingDB
from sqlalchemy.exc import IntegrityError

import unittest


def _make_group(name='foo', **kwargs):
    group = Group(name=name, **kwargs)
    Session.add(group)
    return group


class TestGroupModel(unittest.TestCase):

    def setUp(self):
        initTestingDB()
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_name_is_unique(self):
        _make_group(name='foo')
        _make_group(name='foo')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn('column name is not unique', cm.exception.message)


class TestGroupById(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id(self):
        self.assertEqual(Group.by_id(1), None)
        self.assertEqual(Group.by_id('foo'), None)
        self.assertEqual(Group.by_id(None), None)

    def test_valid_id(self):
        _make_group(name='foo')
        group = Group.by_id(1)
        self.assertEqual(group.name, 'foo')


class TestGroupByName(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_name(self):
        self.assertEqual(Group.by_name(1), None)
        self.assertEqual(Group.by_name('foo'), None)
        self.assertEqual(Group.by_name(None), None)

    def test_valid_name(self):
        _make_group(name='foo')
        group = Group.by_name('foo')
        self.assertEqual(group.name, 'foo')


class TestGroupByProductID(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_product_id(self):
        self.assertEqual(Group.by_product_id(1), None)
        self.assertEqual(Group.by_product_id('foo'), None)
        self.assertEqual(Group.by_product_id(None), None)

    def test_valid_product_id(self):
        _make_group(name='foo', product_id=1)
        group = Group.by_product_id(1)
        self.assertEqual(group.name, 'foo')


class TestGetAll(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_groups(self):
        groups = Group.get_all().all()
        self.assertEqual(len(groups), 0)

    def test_all_groups(self):
        _make_group(name='foo')
        _make_group(name='bar')
        _make_group(name='baz')
        groups = Group.get_all().all()
        self.assertEqual(len(groups), 3)

    def test_ordered_by_name_by_default(self):
        _make_group(name='foo')
        _make_group(name='bar')
        _make_group(name='baz')
        groups = Group.get_all().all()
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups[0].name, 'bar')
        self.assertEqual(groups[1].name, 'baz')
        self.assertEqual(groups[2].name, 'foo')

    def test_override_ordered_by(self):
        _make_group(name='foo')
        _make_group(name='bar')
        _make_group(name='baz')
        groups = Group.get_all(order_by='id').all()
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups[0].name, 'foo')
        self.assertEqual(groups[1].name, 'bar')
        self.assertEqual(groups[2].name, 'baz')

    def test_filter_by(self):
        _make_group(name='foo')
        _make_group(name='bar')
        groups = Group.get_all(filter_by={'name': 'foo'}).all()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, 'foo')

    def test_limit(self):
        _make_group(name='foo')
        _make_group(name='bar')
        groups = Group.get_all(limit=1).all()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, 'bar')


class TestUserProperties(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.group = _make_group()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_get_property(self):
        with self.assertRaises(KeyError) as cm:
            self.group.get_property('foo')
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')

    def test_get_property_with_default_value(self):
        self.assertEqual(
            self.group.get_property('foo', default=u'bar'), u'bar',)

    def test_set_property(self):
        self.group.set_property('foo', u'bar')
        self.assertEqual(self.group.get_property('foo'), u'bar')

        self.group.set_property('foo', u'baz')
        self.assertEqual(self.group.get_property('foo'), u'baz')

    def test_set_property_strict(self):
        with self.assertRaises(KeyError) as cm:
            self.group.set_property('foo', u'bar', strict=True)
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')
