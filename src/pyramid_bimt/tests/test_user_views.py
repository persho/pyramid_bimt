# -*- coding: utf-8 -*-
"""Tests for User views."""

from colanderalchemy import SQLAlchemySchemaNode
from datetime import date
from datetime import datetime
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_user
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from pyramid_bimt.security import verify
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.views.user import UserAdd

import colander
import copy
import mock
import transaction
import unittest


def _make_group(
    id=1,
    name='foo',
):
    return Group(
        id=id,
        name=name,
    )


def _make_property(
    id=1,
    key=u'foo',
    value=u'bar'
):
    return UserProperty(
        id=id,
        key=key,
        value=value,
    )


def _make_audit_log_entry(
    id=1,
    user_id=1,
    event_type_id=1,
    timestamp=datetime(2014, 1, 2, 3, 4, 5),
    comment=u'Foö'
):
    return AuditLogEntry(
        id=id,
        user_id=user_id,
        event_type_id=event_type_id,
        timestamp=timestamp,
        comment=comment,
    )


def _make_user(
    id=1,
    email='foo@bar.com',
    fullname=u'Foö Bar',
    affiliate=u'Aff',
    billing_email='payments@bar.com',
    valid_to=date(2014, 2, 1),
    last_payment=date(2014, 1, 1),
    groups=None,
    properties=None,
    audit_log_entries=None
):
    if not groups:  # pragma: no branch
        groups = [_make_group()]
    if not properties:  # pragma: no branch
        properties = [_make_property()]
    if not audit_log_entries:  # pragma: no branch
        audit_log_entries = [_make_audit_log_entry()]
    return User(
        id=id,
        email=email,
        fullname=fullname,
        affiliate=affiliate,
        billing_email=billing_email,
        valid_to=valid_to,
        last_payment=last_payment,
        groups=groups,
        properties=properties,
        audit_log_entries=audit_log_entries,
    )


class TestUserList(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from pyramid_bimt.views.user import UserView
        self.context = testing.DummyResource()
        self.request = testing.DummyRequest(layout_manager=mock.Mock())
        self.view = UserView(self.context, self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.user.User')
    @mock.patch('pyramid_bimt.views.user.app_assets')
    @mock.patch('pyramid_bimt.views.user.table_assets')
    def test_view_setup(self, table_assets, app_assets, User):
        self.view.__init__(self.context, self.request)
        self.view.list()

        self.assertTrue(self.request.layout_manager.layout.hide_sidebar)
        app_assets.need.assert_called_with()
        table_assets.need.assert_called_with()

    @mock.patch('pyramid_bimt.views.user.User')
    def test_result(self, User):
        User.get_all.return_value.count.return_value = 5
        result = self.view.list()

        self.assertEqual(result, {'count': 5})


class TestUserListAJAX(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        from pyramid_bimt.views.user import UserListAJAX
        from pyramid_bimt import add_routes_user
        from pyramid_bimt import add_routes_group

        add_routes_user(self.config)
        add_routes_group(self.config)
        initTestingDB(groups=True, users=True)
        self.request = testing.DummyRequest()
        self.view = UserListAJAX(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_columns(self):
        self.assertEqual(
            self.view.columns.keys(),
            ['id', 'fullname', 'email', 'groups', 'created', 'modified', 'enable/disable', 'edit'])  # noqa

    def test_populate_columns_enabled(self):
        self.view.populate_columns(User.by_id(2))

        self.assertEqual(
            self.view.columns['id'],
            u'<a href="/user/2/">2</a>'
        )
        self.assertEqual(
            self.view.columns['fullname'],
            u'<a href="/user/2/">Stäff Member</a>'
        )
        self.assertEqual(
            self.view.columns['email'],
            u'<a href="/user/2/">staff@bar.com</a>'
        )
        self.assertEqual(
            self.view.columns['groups'],
            u'<a href="/group/2/edit/">staff</a><span>, </span><a href="/group/3/edit/">enabled</a>'  # noqa
        )
        self.assertIn('Disable', self.view.columns['enable/disable'])

    def test_populate_columns_disabled(self):
        with transaction.manager:
            User.by_id(2).disable()
        self.view.populate_columns(User.by_id(2))

        self.assertEqual(
            self.view.columns['id'],
            u'<a style="text-decoration: line-through" href="/user/2/">2</a>'
        )
        self.assertEqual(
            self.view.columns['fullname'],
            (u'<a style="text-decoration: line-through" href="/user/2/">'
                u'Stäff Member</a>')
        )
        self.assertEqual(
            self.view.columns['email'],
            (u'<a style="text-decoration: line-through" href="/user/2/">'
                u'staff@bar.com</a>')
        )
        self.assertEqual(
            self.view.columns['groups'],
            u'<a href="/group/2/edit/">staff</a>'
        )
        self.assertIn('Enable', self.view.columns['enable/disable'])


class TestUserView(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from pyramid_bimt.views.user import UserView
        self.context = _make_user()
        self.request = testing.DummyRequest(layout_manager=mock.Mock())
        self.view = UserView(self.context, self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.user.app_assets')
    @mock.patch('pyramid_bimt.views.user.table_assets')
    def test_view_setup(self, table_assets, app_assets):
        self.view.__init__(self.context, self.request)
        self.view.list()

        self.assertTrue(self.request.layout_manager.layout.hide_sidebar)
        app_assets.need.assert_called_with()
        table_assets.need.assert_called_with()

    def test_result(self):
        result = self.view.view()
        self.assertEqual(result, {
            'user': self.context,
            'audit_log_entries': self.context.audit_log_entries,
            'properties': self.context.properties,
        })


class TestUserEnable(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        add_routes_user(self.config)
        initTestingDB(users=True, groups=True, auditlog_types=True)

        from pyramid_bimt.views.user import UserView
        self.context = User.by_email('one@bar.com')
        self.request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            user=User.by_email('admin@bar.com'))
        self.view = UserView(self.context, self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_enable_enabled(self):
        self.assertTrue(self.context.enabled)

        result = self.view.enable()
        self.assertTrue(self.context.enabled)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/users/')
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'User "one@bar.com" already enabled, skipping.']
        )

    def test_enable_disabled(self):
        self.context.disable()
        self.assertFalse(self.context.enabled)

        result = self.view.enable()
        self.assertTrue(self.context.enabled)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/users/')
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'User "one@bar.com" enabled.']
        )

        entries = self.context.audit_log_entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'one@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserEnabled')
        self.assertEqual(
            entries[0].comment, u'Manually enabled by admin@bar.com.')

    def test_disable_disabled(self):
        self.context.disable()
        self.assertFalse(self.context.enabled)

        result = self.view.disable()
        self.assertFalse(self.context.enabled)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/users/')
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'User "one@bar.com" already disabled, skipping.']
        )

    def test_disable_enabled(self):
        self.assertTrue(self.context.enabled)

        result = self.view.disable()
        self.assertFalse(self.context.enabled)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/users/')
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'User "one@bar.com" disabled.']
        )

        entries = self.context.audit_log_entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user.email, 'one@bar.com')
        self.assertEqual(entries[0].event_type.name, 'UserDisabled')
        self.assertEqual(
            entries[0].comment, u'Manually disabled by admin@bar.com.')


class TestGroupsValidator(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        # add_routes_user(self.config)
        initTestingDB(groups=True, auditlog_types=True)

        self.request = testing.DummyRequest(user=mock.Mock())

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_admin_and_admins(self):
        from pyramid_bimt.views.user import deferred_groups_validator
        self.request.user.admin = True
        cstruct = [str(Group.by_name('admins').id), ]

        validator = deferred_groups_validator(None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_admins_and_non_admins(self):
        from pyramid_bimt.views.user import deferred_groups_validator
        self.request.user.admin = False
        cstruct = [str(Group.by_name('staff').id), ]

        validator = deferred_groups_validator(None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_non_admin_and_non_admins(self):
        from pyramid_bimt.views.user import deferred_groups_validator
        self.request.user.admin = False
        cstruct = [str(Group.by_name('staff').id), ]

        validator = deferred_groups_validator(None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_non_admin_and_admins(self):
        from pyramid_bimt.views.user import deferred_groups_validator
        self.request.user.admin = False
        cstruct = [str(Group.by_name('admins').id), ]

        validator = deferred_groups_validator(None, {'request': self.request})
        with self.assertRaises(colander.Invalid) as cm:
            validator(None, cstruct)

        self.assertEqual(
            cm.exception.msg,
            'Only admins can add users to "admins" group.',
        )


class TestUserEmailValidators(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB(groups=True, users=True)

        self.request = testing.DummyRequest()

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_valid_email(self):
        from pyramid_bimt.views.user import deferred_user_email_validator

        cstruct = 'test@bar.com'

        validator = deferred_user_email_validator(
            None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_valid_billing_email(self):
        from pyramid_bimt.views.user import deferred_user_billing_email_validator  # noqa

        cstruct = 'test@bar.com'

        validator = deferred_user_billing_email_validator(
            None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_invalid_email(self):
        from pyramid_bimt.views.user import deferred_user_email_validator
        from colander import Invalid

        cstruct = 'fooooooo'

        validator = deferred_user_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(cm.exception.msg, u'Invalid email address')

    def test_invalid_billing_email(self):
        from pyramid_bimt.views.user import deferred_user_billing_email_validator  # noqa
        from colander import Invalid

        cstruct = 'fooooooo'

        validator = deferred_user_billing_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(cm.exception.msg, u'Invalid email address')

    def test_email_already_in_use_by_email(self):
        from pyramid_bimt.views.user import deferred_user_email_validator
        from colander import Invalid

        cstruct = 'admin@bar.com'

        validator = deferred_user_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(
            cm.exception.msg,
            u'Email admin@bar.com is already in use.'
        )

    def test_billing_email_already_in_use_by_email(self):
        from pyramid_bimt.views.user import deferred_user_billing_email_validator  # noqa
        from colander import Invalid

        cstruct = 'admin@bar.com'

        validator = deferred_user_billing_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(
            cm.exception.msg,
            u'Email admin@bar.com is already in use.'
        )

    def test_email_already_in_use_by_billing_email(self):
        from pyramid_bimt.views.user import deferred_user_email_validator
        from colander import Invalid

        cstruct = 'billing@bar.com'

        validator = deferred_user_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(
            cm.exception.msg,
            u'Email billing@bar.com is already in use.'
        )

    def test_billing_email_already_in_use_by_billing_email(self):
        from pyramid_bimt.views.user import deferred_user_billing_email_validator  # noqa
        from colander import Invalid

        cstruct = 'billing@bar.com'

        validator = deferred_user_billing_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(
            cm.exception.msg,
            u'Email billing@bar.com is already in use.'
        )

    def test_context_email_allowed_for_email(self):
        from pyramid_bimt.views.user import deferred_user_email_validator

        schema = SQLAlchemySchemaNode(User)
        self.request.context = User.by_email('one@bar.com')
        self.request.POST['email'] = 'one@bar.com'

        validator = deferred_user_email_validator(
            None, {'request': self.request})

        self.assertFalse(validator(schema.get('email'), 'one@bar.com'))

    def test_context_billing_email_allowed_for_email(self):
        from pyramid_bimt.views.user import deferred_user_email_validator

        schema = SQLAlchemySchemaNode(User)
        self.request.context = User.by_email('one@bar.com')
        self.request.POST['email'] = 'billing@bar.com'

        validator = deferred_user_email_validator(
            None, {'request': self.request})

        self.assertFalse(validator(schema.get('email'), 'billing@bar.com'))

    def test_context_email_allowed_for_billing_email(self):
        from pyramid_bimt.views.user import deferred_user_billing_email_validator  # noqa

        schema = SQLAlchemySchemaNode(User)
        self.request.context = User.by_email('one@bar.com')
        self.request.POST['email'] = 'one@bar.com'

        validator = deferred_user_billing_email_validator(
            None, {'request': self.request})

        self.assertFalse(validator(schema.get('email'), 'one@bar.com'))

    def test_context_billing_email_allowed_for_billing_email(self):
        from pyramid_bimt.views.user import deferred_user_billing_email_validator  # noqa

        schema = SQLAlchemySchemaNode(User)
        self.request.context = User.by_email('one@bar.com')
        self.request.POST['email'] = 'billing@bar.com'

        validator = deferred_user_billing_email_validator(
            None, {'request': self.request})

        self.assertFalse(validator(schema.get('email'), 'billing@bar.com'))


class TestUserAdd(unittest.TestCase):

    APPSTRUCT = {
        'email': 'foo@bar.com',
        'password': 'secret',
        'fullname': u'Foö Bar',
        'affiliate': u'Aff',
        'billing_email': 'payments@bar.com',
        'valid_to': date(2014, 2, 1),
        'last_payment': date(2014, 1, 1),
        'groups': [1, ],
        'properties': [
            {u'key': u'foo', u'value': u'bar'},
            {u'key': u'affiliate_id'},
        ],
    }

    def setUp(self):
        self.config = testing.setUp()
        add_routes_user(self.config)
        initTestingDB(groups=True, auditlog_types=True, users=True)

        self.request = testing.DummyRequest(
            user=User.by_email('admin@bar.com'),
            registry=mock.Mock()
        )
        self.request.registry.notify = mock.Mock()
        self.view = UserAdd(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_groups_choices_admin(self):
        self.view = UserAdd(self.request)
        choices = [
            group for id_, group in self.view.schema['groups'].widget.values
        ]
        self.assertFalse('enabled' in choices)
        self.assertTrue('admins' in choices)

    def test_groups_choices_non_admin(self):
        self.request.user = User.by_email('one@bar.com')
        self.view = UserAdd(self.request)
        choices = [
            group for id_, group in self.view.schema['groups'].widget.values
        ]
        self.assertFalse('enabled' in choices)
        self.assertFalse('admins' in choices)

    def test_appstruct_empty_request(self):
        self.assertEqual(self.view.appstruct(), {})

    def test_appstruct_full_request(self):
        for key, value in self.APPSTRUCT.items():
            self.request.params[key] = value

        self.assertEqual(self.view.appstruct(), self.APPSTRUCT)

    def test_view_csrf_token(self):
        csrf_token_field = self.view.schema.get('csrf_token')
        self.assertIsNotNone(csrf_token_field)
        self.assertEqual(csrf_token_field.title, 'Csrf Token')

    @mock.patch('pyramid_bimt.views.user.UserCreated')
    def test_submit_success(self, UserCreated):
        result = self.view.submit_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/user/4/')
        self.assertTrue(self.request.registry.notify.called)

        user = User.by_id(4)
        self.assertEqual(user.email, 'foo@bar.com')
        self.assertTrue(verify('secret', user.password))
        self.assertEqual(user.fullname, u'Foö Bar')
        self.assertEqual(user.affiliate, u'Aff')
        self.assertEqual(user.billing_email, 'payments@bar.com')
        self.assertEqual(user.valid_to, date(2014, 2, 1))
        self.assertEqual(user.last_payment, date(2014, 1, 1))
        self.assertEqual(user.groups, [Group.by_id(1), ])
        self.assertEqual(user.get_property('foo'), 'bar')
        UserCreated.assert_called_with(
            self.request,
            user,
            'secret',
            u'Created manually by admin@bar.com'
        )

        self.assertEqual(
            self.request.session.pop_flash(), [u'User "foo@bar.com" added.'])


class TestUserEdit(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        add_routes_user(self.config)
        initTestingDB(groups=True, users=True)

        from pyramid_bimt.views.user import UserEdit
        self.request = testing.DummyRequest()
        self.request.user = mock.Mock()
        self.view = UserEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_appstruct_empty_context(self):
        self.request.context = User()
        self.assertEqual(self.view.appstruct(), {})

    def test_appstruct_full_context(self):
        self.request.context = _make_user()
        self.assertEqual(self.view.appstruct(), {
            'email': 'foo@bar.com',
            'fullname': u'Foö Bar',
            'affiliate': u'Aff',
            'billing_email': 'payments@bar.com',
            'valid_to': date(2014, 2, 1),
            'last_payment': date(2014, 1, 1),
            'groups': ['1', ],
            'properties': [
                {'key': u'foo', 'value': u'bar'},
            ],
        })

    def test_view_csrf_token(self):
        csrf_token_field = self.view.schema.get('csrf_token')
        self.assertIsNotNone(csrf_token_field)
        self.assertEqual(csrf_token_field.title, 'Csrf Token')

    APPSTRUCT = {
        'email': 'foo@bar.com',
        'password': 'new_secret',
        'fullname': u'Foö Bar',
        'affiliate': u'Aff',
        'billing_email': 'payments@bar.com',
        'valid_to': date(2014, 2, 1),
        'last_payment': date(2014, 1, 1),
        'groups': [1, ],
        'properties': [
            {u'key': u'foo', u'value': u'bar'},   # existing property
            {u'key': u'baz', u'value': u'bam'},   # new property
            {u'key': u'empty'},   # new property
        ],
    }

    def test_save_success(self):
        self.request.context = User.by_id(2)

        # add a property that will get updated on save_success()
        self.request.context.set_property(key=u'foo', value=u'var')

        result = self.view.save_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/user/2/')

        user = User.by_id(2)
        self.assertEqual(user.email, 'foo@bar.com')
        self.assertTrue(verify('new_secret', user.password))
        self.assertEqual(user.fullname, u'Foö Bar')
        self.assertEqual(user.affiliate, u'Aff')
        self.assertEqual(user.billing_email, 'payments@bar.com')
        self.assertEqual(user.valid_to, date(2014, 2, 1))
        self.assertEqual(user.last_payment, date(2014, 1, 1))
        self.assertEqual(user.groups, [Group.by_id(1), Group.by_id(3)])  # enabled user stays enabled  # noqa
        self.assertEqual(user.get_property('foo'), 'bar')
        self.assertEqual(user.get_property('baz'), 'bam')
        self.assertEqual(user.get_property('empty'), None)
        with self.assertRaises(KeyError):
            user.get_property('bimt')  # removed property

        self.assertEqual(
            self.request.session.pop_flash(),
            [u'User "foo@bar.com" modified.'],
        )

    def test_save_success_disabled_stays_disabled(self):
        self.request.context = User.by_id(2)
        self.request.context.disable()

        result = self.view.save_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/user/2/')

        user = User.by_id(2)

        self.assertEqual(user.groups, [Group.by_id(1)])
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'User "foo@bar.com" modified.'],
        )

    def test_empty_password_field(self):
        self.request.context = User.by_id(2)

        # simulate that password field was left empty
        appstruct = copy.deepcopy(self.APPSTRUCT)
        appstruct['password'] = ''

        # submit form
        self.view.save_success(appstruct)

        # assert that secret fields remained unchanged
        user = User.by_id(2)
        self.assertEqual(user.email, 'foo@bar.com')
        self.assertTrue(verify('secret', user.password))


class TestUserUnsubscribe(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        add_routes_user(self.config)
        initTestingDB(users=True, groups=True, auditlog_types=True)

        from pyramid_bimt.views.user import UserView
        self.context = User.by_id(2)
        self.request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            user=self.context
        )
        self.context.request = self.request
        self.view = UserView(self.context, self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_unsubscribe(self):
        self.assertFalse(self.context.unsubscribed)

        result = self.view.unsubscribe()
        self.assertTrue(self.context.unsubscribed)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/')
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'You have been unsubscribed from newsletter.']
        )

        result = self.view.unsubscribe()
        self.assertTrue(self.context.unsubscribed)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/')
        self.assertEqual(
            self.request.session.pop_flash(),
            [u'You are already unsubscribed from newsletter.']
        )
