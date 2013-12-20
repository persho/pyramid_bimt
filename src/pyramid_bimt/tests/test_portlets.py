# -*- coding: utf-8 -*-
"""Tests for pyramid_bimt portlet views."""

from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid_basemodel import Session
from pyramid_bimt import configure
from pyramid_bimt.models import Group
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB
from sqlalchemy.exc import IntegrityError

import unittest
import transaction
import webtest


def _make_group(name='foo'):
    group = Group(name=name)
    Session.add(group)
    return group


def _make_user(email='foo@bar.com', groups=None):
    if not groups:
        groups = []
    user = User(email=email, groups=groups)
    Session.add(user)
    return user


def _make_portlet(name='foo', groups=None, position='top', weight=0):
    if not groups:
        groups = []
    portlet = Portlet(name=name, groups=groups, position=position, weight=0)
    Session.add(portlet)
    return portlet


class TestPortletModel(unittest.TestCase):

    def setUp(self):
        initTestingDB()
        self.config = testing.setUp()

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


class TestPortletEnabled(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.portlet = Portlet()

    def tearDown(self):
        testing.tearDown()

    def test_portlet_enabled(self):
        self.portlet.groups = [Group(name='foo'), Group(name='bar')]
        self.assertTrue(self.portlet.enabled)

    def test_portlet_disabled(self):
        self.portlet.groups = []
        self.assertFalse(self.portlet.enabled)


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


class TestByUserAndPosition(unittest.TestCase):

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
        _make_portlet(name='foo', groups=[group, ], position='top')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'top')
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')

    def test_position_filter(self):
        group = _make_group()
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[group, ], position='top')
        _make_portlet(name='bar', groups=[group, ], position='bottom')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'top')
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')

    def test_group_filter(self):
        group = _make_group()
        other_group = _make_group(name='other')
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[group, ], position='top')
        _make_portlet(name='bar', groups=[other_group, ], position='top')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'top')
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')

    def test_no_position(self):
        group = _make_group()
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[group], position='')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'top')
        self.assertEqual(len(portlets), 0)

    def test_no_group(self):
        group = _make_group()
        _make_user(groups=[group, ])
        _make_portlet(name='foo', groups=[], position='top')
        portlets = Portlet.by_user_and_position(User.by_id(1), 'top')
        self.assertEqual(len(portlets), 0)


class TestGetAll(unittest.TestCase):

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
        _make_portlet(name='foo', position='c')
        _make_portlet(name='bar', position='a')
        _make_portlet(name='baz', position='b')
        portlets = Portlet.get_all()
        self.assertEqual(len(portlets), 3)
        self.assertEqual(portlets[0].name, 'bar')
        self.assertEqual(portlets[1].name, 'baz')
        self.assertEqual(portlets[2].name, 'foo')

    def test_override_ordered_by(self):
        _make_portlet(name='foo', weight=3)
        _make_portlet(name='bar', weight=2)
        _make_portlet(name='baz', weight=-1)
        portlets = Portlet.get_all(order_by='weight')
        self.assertEqual(len(portlets), 3)
        self.assertEqual(portlets[0].name, 'foo')
        self.assertEqual(portlets[1].name, 'bar')
        self.assertEqual(portlets[2].name, 'baz')

    def test_filter_by(self):
        _make_portlet(name='foo', position='top')
        _make_portlet(name='bar', position='bottom')
        portlets = Portlet.get_all(filter_by={'position': 'top'})
        self.assertEqual(len(portlets), 1)
        self.assertEqual(portlets[0].name, 'foo')


class TestPortletsFunctional(unittest.TestCase):
    def setUp(self):
        settings = {
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB(groups=True, users=True)
        configure(self.config)
        app = self.config.make_wsgi_app()
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_edit_nonexisting_portlet(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)
        self.assertRaises(
            HTTPNotFound, self.testapp.get, '/portlets/123456789/edit')

    def test_add_portlet(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)

        resp = self.testapp.get('/portlets/add', status=200)
        self.assertIn('<h1>Add Portlet</h1>', resp.text)

        # add portlet
        form = resp.forms['portletedit']
        form['name'] = 'portlet-foo'
        form['html'] = u'<p>Foö</p>'

        form.get('checkbox', index=0).checked = True
        self.assertEqual(form.get('checkbox', index=0).value, u'admins')

        form['deformField3'] = u'above_content'

        resp = form.submit('save')

        # assert redirect to /portlets
        self.assertEqual(resp.status, '302 Found')
        self.assertEqual(resp.location, 'http://localhost/portlets')
        resp = resp.follow()

        # assert portlet was created
        self.assertIn("""<td>1</td>
          <td>portlet-foo</td>
          <td>admins</td>
          <td>above_content</td>""", resp.text)

        # assert portlet is visible on page for admin
        resp = self.testapp.get('/login', status=200)
        self.assertIn(u'<p>Foö</p>', resp.text)

        # assert portlet is not visible on page for normal user
        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        resp = self.testapp.get('/login', status=200)
        self.assertNotIn(u'<p>Foö</p>', resp.text)

    def test_edit_portlet(self):
        self.config.testing_securitypolicy(
            userid='admin@bar.com', permissive=True)

        admins = Group.by_name('admins')
        _make_portlet(
            name='portlet-foo', groups=[admins, ], position='above_footer')
        transaction.commit()

        # edit portlet
        resp = self.testapp.get('/portlets/1/edit', status=200)
        form = resp.forms['portletedit']
        form['name'] = 'portlet-bar'
        form['html'] = u'<p>Bär</p>'

        form.get('checkbox', index=1).checked = True
        self.assertEqual(form.get('checkbox', index=1).value, u'users')

        form['deformField3'] = u'above_footer'

        resp = form.submit('save')
        resp = resp.follow()

        # assert portlet was modified
        self.assertIn("""<td>1</td>
          <td>portlet-bar</td>
          <td>admins, users</td>
          <td>above_footer</td>""", resp.text)

        resp = self.testapp.get('/login', status=200)
        self.assertIn(u'<p>Bär</p>', resp.text)
