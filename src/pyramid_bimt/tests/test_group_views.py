# -*- coding: utf-8 -*-
"""Tests for Group views."""

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_group
from pyramid_bimt.models import Group
from pyramid_bimt.models import GroupProperty
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB

import mock
import unittest


def _make_group(
    name='foo',
    product_id=13,
    validity=31,
    trial_validity=7,
    forward_ipn_to_url='http://example.com',
    properties=None,
):
    if not properties:  # pragma: no branch
        properties = [_make_property()]
    return Group(
        name=name,
        product_id=product_id,
        validity=validity,
        trial_validity=trial_validity,
        forward_ipn_to_url='http://example.com',
        properties=properties,
    )


def _make_property(
    id=1,
    key=u'foo',
    value=u'bar'
):
    return GroupProperty(
        id=id,
        key=key,
        value=value,
    )


class TestGroupList(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from pyramid_bimt.views.group import GroupView
        self.context = testing.DummyResource()
        self.request = testing.DummyRequest(layout_manager=mock.Mock())
        self.view = GroupView(self.context, self.request)

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.group.Group')
    @mock.patch('pyramid_bimt.views.group.app_assets')
    @mock.patch('pyramid_bimt.views.group.table_assets')
    def test_view_setup(self, table_assets, app_assets, Group):
        Group.get_all.return_value.all.return_value = []
        self.view.__init__(self.context, self.request)
        self.view.list()

        self.assertTrue(self.request.layout_manager.layout.hide_sidebar)
        app_assets.need.assert_called_with()
        table_assets.need.assert_called_with()

    @mock.patch('pyramid_bimt.views.group.Group')
    def test_result(self, Group):
        group = _make_group()
        Group.get_all.return_value.all.return_value = [group, ]
        result = self.view.list()

        self.assertEqual(result, {
            'groups': [group, ],
        })


class TestGroupAdd(unittest.TestCase):

    APPSTRUCT = {
        'name': 'foo',
        'product_id': 13,
        'validity': 30,
        'trial_validity': 7,
        'forward_ipn_to_url': 'http://example.com',
        'users': [1, ],
        'properties': [{u'key': u'foo', u'value': u'bar'}, ],
    }

    def setUp(self):
        self.config = testing.setUp()
        add_routes_group(self.config)
        initTestingDB(groups=True, users=True)

        from pyramid_bimt.views.group import GroupAdd
        self.request = testing.DummyRequest()
        self.view = GroupAdd(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_appstruct_empty_request(self):
        self.assertEqual(self.view.appstruct(), {})

    def test_appstruct_full_request(self):
        for key, value in self.APPSTRUCT.items():
            self.request.params[key] = value

        self.assertEqual(self.view.appstruct(), self.APPSTRUCT)

    def test_submit_success(self):
        result = self.view.submit_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/group/6/edit')

        group = Group.by_id(6)
        self.assertEqual(group.name, 'foo')
        self.assertEqual(group.product_id, 13)
        self.assertEqual(group.validity, 30)
        self.assertEqual(group.trial_validity, 7)
        self.assertEqual(group.forward_ipn_to_url, 'http://example.com')
        self.assertEqual(group.users, [User.by_id(1), ])
        self.assertEqual(group.get_property('foo'), 'bar')

        self.assertEqual(
            self.request.session.pop_flash(), [u'Group "foo" added.'])


class TestGroupEdit(unittest.TestCase):

    APPSTRUCT = {
        'name': 'foo',
        'product_id': 13,
        'validity': 31,
        'trial_validity': 7,
        'forward_ipn_to_url': 'http://example.com',
        'users': [2, ],
        'properties': [
            {u'key': u'foo', u'value': u'bar'},   # existing property
            {u'key': u'baz', u'value': u'bam'},   # new property
        ],
    }

    def setUp(self):
        self.config = testing.setUp()
        add_routes_group(self.config)
        initTestingDB(groups=True, users=True)

        from pyramid_bimt.views.group import GroupEdit
        self.request = testing.DummyRequest()
        self.view = GroupEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_appstruct_empty_context(self):
        self.request.context = Group()
        self.assertEqual(self.view.appstruct(), {})

    def test_appstruct_full_context(self):
        self.request.context = _make_group()
        self.request.context.users = [User.by_email('one@bar.com'), ]
        self.assertEqual(self.view.appstruct(), {
            'name': 'foo',
            'product_id': 13,
            'validity': 31,
            'trial_validity': 7,
            'forward_ipn_to_url': 'http://example.com',
            'users': ['3', ],
            'properties': [{'key': u'foo', 'value': u'bar'}, ],
        })

    def test_save_success(self):
        self.request.context = Group.by_id(1)

        # add a property that will get updated on save_success()
        self.request.context.set_property(key=u'foo', value=u'var')

        result = self.view.save_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/group/1/edit')

        group = Group.by_id(1)
        self.assertEqual(group.name, 'foo')
        self.assertEqual(group.product_id, 13)
        self.assertEqual(group.validity, 31)
        self.assertEqual(group.trial_validity, 7)
        self.assertEqual(group.forward_ipn_to_url, 'http://example.com')
        self.assertEqual(group.users, [User.by_id(2), ])
        self.assertEqual(group.get_property('foo'), 'bar')
        self.assertEqual(group.get_property('baz'), 'bam')
        self.assertEqual(
            self.request.session.pop_flash(), [u'Group "foo" modified.'])

    def test_save_success_remove_properties(self):
        self.request.context = Group.by_id(1)

        self.APPSTRUCT['properties'] = []
        result = self.view.save_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/group/1/edit')

        group = Group.by_id(1)
        self.assertEqual(group.name, 'foo')
        self.assertEqual(group.product_id, 13)
        self.assertEqual(group.validity, 31)
        self.assertEqual(group.trial_validity, 7)
        self.assertEqual(group.forward_ipn_to_url, 'http://example.com')
        self.assertEqual(group.users, [User.by_id(2), ])
        self.assertIsNone(group.get_property('foo', None))
        self.assertEqual(
            self.request.session.pop_flash(), [u'Group "foo" modified.'])
