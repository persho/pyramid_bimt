# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt portlet views."""

from pyramid import testing
from pyramid_basemodel import Session
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.tests.test_group_model import _make_group
from pyramid_bimt.tests.test_user_model import _make_user
from sqlalchemy.exc import IntegrityError

import unittest


def _make_portlet(name='foo', **kwargs):
    portlet = Portlet(name=name, **kwargs)
    Session.add(portlet)
    return portlet


class TestPortletModel(unittest.TestCase):

    def setUp(self):
        initTestingDB()
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_default_values(self):
        portlet = _make_portlet()
        Session.flush()
        self.assertEqual(portlet.html, u'')
        self.assertEqual(portlet.weight, 0)

    def test_name_is_unique(self):
        _make_portlet(name='foo')
        _make_portlet(name='foo')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn('column name is not unique', cm.exception.message)

    def test_render_portlet(self):
        portlet = _make_portlet(name='foo', html=u'fööbär')
        self.assertEqual(
            portlet.get_rendered_portlet(),
            u'<div class="well">f\xf6\xf6b\xe4r</div>\n'
        )

    def test__repr__(self):
        self.assertEqual(
            repr(_make_portlet(id=1, name='foo')),
            '<Portlet:1 (name=\'foo\')>',
        )


class TestPortletById(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_id(self):
        self.assertEqual(Portlet.by_id(1), None)
        self.assertEqual(Portlet.by_id('foo'), None)
        self.assertEqual(Portlet.by_id(None), None)

    def test_valid_id(self):
        _make_portlet(name='foo')
        portlet = Portlet.by_id(1)
        self.assertEqual(portlet.name, 'foo')


class TestPortletByUserAndPosition(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_user(self):
        portlets = Portlet.by_user_and_position(None, 'above_content')
        self.assertEqual(portlets, [])

    def test_invalid_position(self):
        portlets = Portlet.by_user_and_position(User(), 'foo')
        self.assertEqual(portlets, [])

    def test_valid_user_and_position(self):
        group = _make_group()
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[group, ], position='above_content')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'above_content')
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')

    def test_position_filter(self):
        group = _make_group()
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[group, ], position='above_content')
        _make_portlet(name='bar', groups=[group, ], position='above_footer')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'above_content')
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')

    def test_group_filter(self):
        group = _make_group()
        other_group = _make_group(name='other')
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[group, ], position='above_content')
        _make_portlet(name='bar', groups=[other_group, ], position='above_content')  # noqa
        portlets = Portlet.by_user_and_position(User.by_id(1), 'above_content')
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')

    def test_no_group(self):
        group = _make_group()
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[], position='above_content')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'above_content')
        self.assertEqual(len(portlets), 0)


class TestPortletGetAll(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_portlets(self):
        portlets = Portlet.get_all()
        self.assertEqual(len(portlets), 0)

    def test_all_portlets(self):
        _make_portlet(name='foo')
        _make_portlet(name='bar')
        _make_portlet(name='baz')
        portlets = Portlet.get_all()
        self.assertEqual(len(portlets), 3)

    def test_ordered_by_position_by_default(self):
        _make_portlet(name='foo', position='above_content')
        _make_portlet(name='bar', position='above_footer')
        _make_portlet(name='baz', position='below_sidebar')
        portlets = Portlet.get_all()
        self.assertEqual(len(portlets), 3)
        self.assertEqual(portlets[0].name, 'foo')
        self.assertEqual(portlets[1].name, 'bar')
        self.assertEqual(portlets[2].name, 'baz')

    def test_override_ordered_by(self):
        _make_portlet(name='foo', weight=3)
        _make_portlet(name='bar', weight=2)
        _make_portlet(name='baz', weight=-1)
        portlets = Portlet.get_all(order_by='weight')
        self.assertEqual(len(portlets), 3)
        self.assertEqual(portlets[0].name, 'baz')
        self.assertEqual(portlets[1].name, 'bar')
        self.assertEqual(portlets[2].name, 'foo')

    def test_filter_by(self):
        _make_portlet(name='foo', position='above_content')
        _make_portlet(name='bar', position='above_footer')
        portlets = Portlet.get_all(filter_by={'position': 'above_content'})
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')
