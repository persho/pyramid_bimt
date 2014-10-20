# -*- coding: utf-8 -*-
"""Tests for Portlet views."""

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_portlet
from pyramid_bimt.models import Group
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import PortletPositions
from pyramid_bimt.testing import initTestingDB

import mock
import unittest


def _make_group(
    id=1,
    name='foo',
):
    return Group(
        id=id,
        name=name,
    )


def _make_portlet(
    id=1,
    name='foo',
    groups=None,
    exclude_groups=None,
    position=PortletPositions.below_sidebar,
    weight=0,
    html=u'Foo Portlet'
):
    if not groups:  # pragma: no branch
        groups = [_make_group()]
    if exclude_groups is None:
        exclude_groups = []
    return Portlet(
        id=id,
        name=name,
        groups=groups,
        exclude_groups=exclude_groups,
        position=position,
        weight=weight,
        html=html,
    )


class TestPortletList(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from pyramid_bimt.views.portlet import PortletView
        self.context = testing.DummyResource()
        self.request = testing.DummyRequest(layout_manager=mock.Mock())
        self.view = PortletView(self.context, self.request)

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.portlet.Portlet')
    @mock.patch('pyramid_bimt.views.portlet.app_assets')
    @mock.patch('pyramid_bimt.views.portlet.table_assets')
    def test_view_setup(self, table_assets, app_assets, Portlet):
        Portlet.query.order_by.return_value.all.return_value = []
        self.view.__init__(self.context, self.request)
        self.view.list()

        self.assertTrue(self.request.layout_manager.layout.hide_sidebar)
        app_assets.need.assert_called_with()
        table_assets.need.assert_called_with()

    @mock.patch('pyramid_bimt.views.portlet.Portlet')
    def test_result(self, Portlet):
        portlet = _make_portlet()
        Portlet.query.order_by.return_value.all.return_value = [portlet, ]
        result = self.view.list()

        self.assertEqual(result, {
            'positions': PortletPositions,
            'portlets': [portlet, ],
        })


class TestPortletAdd(unittest.TestCase):

    APPSTRUCT = {
        'name': 'foo',
        'groups': [1, ],
        'exclude_groups': [2, ],
        'position': 'below_sidebar',
        'weight': 10,
        'html': u'Foo',
    }

    def setUp(self):
        self.config = testing.setUp()
        add_routes_portlet(self.config)
        self.config.include('pyramid_chameleon')
        initTestingDB(groups=True)

        from pyramid_bimt.views.portlet import PortletAdd
        self.request = testing.DummyRequest()
        self.view = PortletAdd(self.request)

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
        self.assertEqual(result.location, '/portlet/1/edit/')

        portlet = Portlet.by_id(1)
        self.assertEqual(portlet.name, 'foo')
        self.assertEqual(portlet.groups, [Group.by_id(1)])
        self.assertEqual(portlet.exclude_groups, [Group.by_id(2)])
        self.assertEqual(portlet.position, PortletPositions.below_sidebar.name)
        self.assertEqual(portlet.weight, 10)
        self.assertEqual(portlet.html, u'Foo')

        self.assertEqual(
            self.request.session.pop_flash(), [u'Portlet "foo" added.'])


class TestPortletEdit(unittest.TestCase):

    APPSTRUCT = {
        'name': 'bar',
        'groups': [2, 3],
        'exclude_groups': [4, ],
        'position': 'above_content',
        'weight': -10,
        'html': u'Bar',
    }

    def setUp(self):
        self.config = testing.setUp()
        add_routes_portlet(self.config)
        self.config.include('pyramid_chameleon')
        initTestingDB(groups=True, portlets=True)

        from pyramid_bimt.views.portlet import PortletEdit
        self.request = testing.DummyRequest()
        self.view = PortletEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_appstruct_empty_context(self):
        self.request.context = Portlet()
        self.assertEqual(self.view.appstruct(), {})

    def test_appstruct_full_context(self):
        self.request.context = Portlet.by_id(1)
        self.assertEqual(self.view.appstruct(), {
            'name': 'dummy',
            'groups': ['1', ],
            'exclude_groups': ['3', ],
            'position': PortletPositions.below_sidebar.name,
            'weight': -127,
            'html': u'You are admin.',
        })

    def test_save_success(self):
        self.request.context = Portlet.by_id(1)

        result = self.view.save_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/portlet/1/edit/')

        portlet = Portlet.by_id(1)
        self.assertEqual(portlet.name, 'bar')
        self.assertEqual(portlet.groups, [Group.by_id(2), Group.by_id(3)])
        self.assertEqual(portlet.exclude_groups, [Group.by_id(4), ])
        self.assertEqual(portlet.position, PortletPositions.above_content.name)
        self.assertEqual(portlet.weight, -10)
        self.assertEqual(portlet.html, u'Bar')
        self.assertEqual(
            self.request.session.pop_flash(), [u'Portlet "bar" modified.'])
