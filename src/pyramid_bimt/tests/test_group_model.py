# -*- coding: utf-8 -*-
"""Tests for the Group model."""

from pyramid import testing
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import GroupProperty
from pyramid_bimt.testing import initTestingDB
from sqlalchemy.exc import IntegrityError

import mock
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

    def test_acl_admin(self):
        from pyramid.security import ALL_PERMISSIONS
        group = _make_group(name='admins')
        self.assertEqual(
            group.__acl__,
            [
                (Allow, 'g:admins', ALL_PERMISSIONS),
                DENY_ALL,
            ])

    def test_acl_non_admin(self):
        group = _make_group(name='not-admins')
        self.assertEqual(group.__acl__, [])  # traverse to GroupFactory's acl

    def test__repr__(self):
        self.assertEqual(
            repr(_make_group(id=1, name='foo')),
            '<Group:1 (name=\'foo\')>',
        )

    def test_using_by_id_mixin(self):
        from pyramid_bimt.models import Group
        from pyramid_bimt.models import GetByIdMixin

        self.assertTrue(issubclass(Group, GetByIdMixin))

    def test_using_by_name_mixin(self):
        from pyramid_bimt.models import Group
        from pyramid_bimt.models import GetByNameMixin

        self.assertTrue(issubclass(Group, GetByNameMixin))


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


class TestGroupProperties(unittest.TestCase):

    def setUp(self):
        initTestingDB()
        self.config = testing.setUp()
        self.group = _make_group()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test__repr__(self):
        self.assertEqual(
            repr(GroupProperty(id=1, key=u'foo', value=u'bar')),
            '<GroupProperty:1 (key=u\'foo\', value=u\'bar\')>',
        )

    def test_unique_constraint(self):
        Session.add(GroupProperty(key='foo', group_id=1))
        Session.flush()
        with self.assertRaises(IntegrityError) as cm:
            Session.add(GroupProperty(key='foo', group_id=1))
            Session.flush()
        self.assertIn('key, group_id are not unique', cm.exception.message)

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

    @mock.patch('pyramid_bimt.security.get_current_registry')
    def test_set_property_secure(self, get_current_registry):
        get_current_registry.return_value.settings = {
            'bimt.encryption_aes_16b_key': 'abcdabcdabcdabcd',
        }
        self.group.set_property(u'foo', u'bar', secure=True)
        self.assertEqual(self.group.get_property('foo', secure=True), u'bar')
        self.assertNotEqual(
            self.group.get_property('foo', secure=False), u'bar')

    def test_set_property_strict(self):
        with self.assertRaises(KeyError) as cm:
            self.group.set_property('foo', u'bar', strict=True)
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')
