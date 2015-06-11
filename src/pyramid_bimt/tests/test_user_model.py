# -*- coding: utf-8 -*-
"""Tests for the User model."""

from datetime import date
from pyramid import testing
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.tests.test_group_model import _make_group
from sqlalchemy.exc import IntegrityError

import mock
import unittest


def _make_user(email='foo@bar.com', **kwargs):
    user = User(email=email, **kwargs)
    Session.add(user)
    return user


class TestUserModel(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        initTestingDB(groups=True, users=True)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_default_values(self):
        user = _make_user()
        Session.flush()
        self.assertEqual(user.valid_to, date.today())

    def test_email_is_unique(self):
        _make_user(email='foo@bar.com')
        _make_user(email='foo@bar.com')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn('column email is not unique', cm.exception.message)

    def test_billing_email_is_unique(self):
        _make_user(billing_email='foo@bar.com')
        _make_user(billing_email='foo@bar.com')
        with self.assertRaises(IntegrityError) as cm:
            Session.flush()
        self.assertIn(
            'column billing_email is not unique', cm.exception.message)

    def test_acl_admin(self):
        from pyramid.security import ALL_PERMISSIONS
        user = _make_user(email='foo@bar.com')
        user.groups = [_make_group(name='admins')]
        self.assertEqual(
            user.__acl__,
            [
                (Allow, 'g:admins', ALL_PERMISSIONS),
                DENY_ALL,
            ])

    def test_acl_non_admin(self):
        user = _make_user(email='foo@bar.com')
        user.groups = []
        self.assertEqual(user.__acl__, [])  # traverse to UserFactory's acl

    def test__repr__(self):
        self.assertEqual(
            repr(_make_user(id=1, email='foo@bar.com')),
            '<User:1 (email=\'foo@bar.com\')>',
        )

    def test_using_by_id_mixin(self):
        from pyramid_bimt.models import User
        from pyramid_bimt.models import GetByIdMixin

        self.assertTrue(issubclass(User, GetByIdMixin))


class TestUserByEmail(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_invalid_email(self):
        self.assertEqual(User.by_email(1), None)
        self.assertEqual(User.by_email('foo@bar.com'), None)
        self.assertEqual(User.by_email(None), None)

    def test_valid_email(self):
        _make_user(email='foo@bar.com')
        user = User.by_email(email='foo@bar.com')
        self.assertEqual(user.email, 'foo@bar.com')


class TestUserGetAll(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_users(self):
        users = User.get_all().all()
        self.assertEqual(len(users), 0)

    def test_all_users(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all().all()
        self.assertEqual(len(users), 3)

    def test_ordered_by_email_by_default(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all().all()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].email, 'bar@bar.com')
        self.assertEqual(users[1].email, 'baz@bar.com')
        self.assertEqual(users[2].email, 'foo@bar.com')

    def test_override_ordered_by(self):
        _make_user(email='foo@bar.com', fullname=u'A')
        _make_user(email='bar@bar.com', fullname=u'C')
        _make_user(email='baz@bar.com', fullname=u'B')
        users = User.get_all(order_by='fullname').all()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].fullname, 'A')
        self.assertEqual(users[1].fullname, 'B')
        self.assertEqual(users[2].fullname, 'C')

    def test_ordered_by_created(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all(order_by='created').all()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].email, 'foo@bar.com')
        self.assertEqual(users[1].email, 'bar@bar.com')
        self.assertEqual(users[2].email, 'baz@bar.com')

    def test_ordered_by_modified(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all(order_by='modified', order_direction='desc').all()
        self.assertEqual(len(users), 3)
        self.assertEqual(users[0].email, 'baz@bar.com')
        self.assertEqual(users[1].email, 'bar@bar.com')
        self.assertEqual(users[2].email, 'foo@bar.com')

    def test_filter_by(self):
        _make_user(email='foo@bar.com', affiliate=u'John')
        _make_user(email='bar@bar.com', affiliate=u'Jane')
        users = User.get_all(filter_by={'affiliate': u'John'}).all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].affiliate, 'John')

    def test_limit(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        users = User.get_all(limit=1).all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'bar@bar.com')

    def test_offset(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all(offset=(1, 2)).all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'baz@bar.com')

    def test_search_email(self):
        _make_user(email='foo@bar.com')
        _make_user(email='bar@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all(search='baz').all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'baz@bar.com')

    def test_search_fullname(self):
        _make_user(email='foo@bar.com', fullname=u'aaaaa')
        _make_user(email='bar@bar.com', fullname=u'ccccc')
        _make_user(email='baz@bar.com', fullname=u'bbbbb')
        users = User.get_all(search='ccccc').all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'bar@bar.com')

    def test_search_fullname_case_insensitive(self):
        _make_user(email='foo@bar.com', fullname=u'AAAAA')
        _make_user(email='bar@bar.com', fullname=u'aaaaa')
        _make_user(email='baz@bar.com', fullname=u'BBBBB')
        _make_user(email='foobar@bar.com', fullname=u'bbbbb')
        users = User.get_all(search='aaaaa').all()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].email, 'bar@bar.com')
        self.assertEqual(users[1].email, 'foo@bar.com')
        users = User.get_all(search='AAAAA').all()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].email, 'bar@bar.com')
        self.assertEqual(users[1].email, 'foo@bar.com')

    def test_search_email_case_insensitive(self):
        _make_user(email='foo@bar.com')
        _make_user(email='baz@bar.com')
        users = User.get_all(search='bAZ').all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'baz@bar.com')

    def test_search_email_and_fullname(self):
        _make_user(email='foo@bar.com', fullname=u'aaaaa')
        _make_user(email='bar@bar.com', fullname=u'ccccc')
        _make_user(email='ccccc@bar.com', fullname=u'bbbbb')
        users = User.get_all(search='ccccc').all()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].email, 'bar@bar.com')
        self.assertEqual(users[1].email, 'ccccc@bar.com')


class TestAdmin(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_is_admin(self):
        self.assertTrue(User.by_email('admin@bar.com').admin)

    def test_user_is_not_admin(self):
        self.assertFalse(User.by_email('staff@bar.com').admin)
        self.assertFalse(User.by_email('one@bar.com').admin)


class TestStaff(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_is_staff_member(self):
        self.assertTrue(User.by_email('staff@bar.com').staff)
        self.assertTrue(User.by_email('admin@bar.com').staff)

    def test_user_is_not_staff_member(self):
        self.assertFalse(User.by_email('one@bar.com').staff)


class TestProductGroup(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_product_group(self):
        self.assertIsNone(User.by_email('one@bar.com').product_group)

    def test_single_product_group(self):
        product_group = _make_group(name='foo', product_id='foo')
        product_group.users.append(User.by_email('one@bar.com'))
        self.assertEqual(
            User.by_email('one@bar.com').product_group.name, 'foo')

    def test_multiple_product_groups(self):
        product_group_foo = _make_group(name='foo', product_id='foo')
        product_group_bar = _make_group(name='bar', product_id='bar')
        product_group_foo.users.append(User.by_email('one@bar.com'))
        product_group_bar.users.append(User.by_email('one@bar.com'))

        from sqlalchemy.orm.exc import MultipleResultsFound
        with self.assertRaises(MultipleResultsFound):
            User.by_email('one@bar.com').product_group


class TestTrial(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_is_trial(self):
        self.assertTrue(User.by_email('one@bar.com').trial)

    def test_user_is_not_trial(self):
        self.assertFalse(User.by_email('admin@bar.com').trial)


class TestEnabledDisabled(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()
        self.user = _make_user()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_enable(self):
        self.assertFalse(self.user.enabled)
        self.user.enable()
        self.assertTrue(self.user.enabled)

    def test_user_disable(self):
        self.test_user_enable()
        self.assertTrue(self.user.enabled)
        self.user.disable()
        self.assertFalse(self.user.enabled)

    def test_get_enabled(self):
        enabled = User.get_enabled()
        self.assertEqual(len(enabled), 3)
        self.assertItemsEqual(
            [user.email for user in enabled],
            ['admin@bar.com', 'staff@bar.com', 'one@bar.com'],
        )


class TestSubscription(unittest.TestCase):

    def setUp(self):
        initTestingDB(users=True, groups=True)
        self.config = testing.setUp()
        self.user = _make_user()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_user_unsubscribe(self):
        self.assertFalse(self.user.unsubscribed)
        self.assertTrue(self.user.unsubscribe())
        self.assertFalse(self.user.unsubscribe())
        self.assertTrue(self.user.unsubscribed)

    def test_user_subscribe(self):
        self.test_user_unsubscribe()
        self.assertTrue(self.user.unsubscribed)
        self.assertTrue(self.user.subscribe())
        self.assertFalse(self.user.subscribe())
        self.assertFalse(self.user.unsubscribed)


class TestUserProperties(unittest.TestCase):

    def setUp(self):
        initTestingDB()
        self.config = testing.setUp()
        self.user = _make_user()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_unique_constraint(self):
        Session.add(UserProperty(key='foo', user_id=1))
        Session.flush()
        with self.assertRaises(IntegrityError) as cm:
            Session.add(UserProperty(key='foo', user_id=1))
            Session.flush()
        self.assertIn('key, user_id are not unique', cm.exception.message)

    def test_get_property(self):
        with self.assertRaises(KeyError) as cm:
            self.user.get_property('foo')
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')

    def test_get_property_with_default_value(self):
        self.assertEqual(
            self.user.get_property('foo', default=u'bar'), u'bar',)

    def test_set_property(self):
        self.user.set_property('foo', u'bar')
        self.assertEqual(self.user.get_property('foo'), u'bar')

        self.user.set_property('foo', u'baz')
        self.assertEqual(self.user.get_property('foo'), u'baz')

    @mock.patch('pyramid_bimt.security.get_current_registry')
    def test_set_property_secure(self, get_current_registry):
        get_current_registry.return_value.settings = {
            'bimt.encryption_aes_16b_key': 'abcdabcdabcdabcd',
        }
        self.user.set_property('foo', u'bar', secure=True)
        self.assertEqual(self.user.get_property('foo', secure=True), u'bar')
        self.assertNotEqual(
            self.user.get_property('foo', secure=False), u'bar')

    def test_set_property_strict(self):
        with self.assertRaises(KeyError) as cm:
            self.user.set_property('foo', u'bar', strict=True)
        self.assertEqual(cm.exception.message, 'Property "foo" not found.')

    def test__repr__(self):
        self.assertEqual(
            repr(UserProperty(id=1, key=u'foo', value=u'bar')),
            '<UserProperty:1 (key=u\'foo\', value=u\'bar\')>',
        )

    def test_has_property(self):
        self.assertFalse(self.user.has_property('foo'))

        self.user.set_property('foo', u'bar')
        self.assertTrue(self.user.has_property('foo'))
