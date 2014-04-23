# -*- coding: utf-8 -*-
"""Tests for Mailing views."""

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid_basemodel import Session
from pyramid_bimt import add_routes_mailing
from pyramid_bimt import add_routes_user
from pyramid_bimt.models import Group
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import MailingTriggers
from pyramid_bimt.models import User
from pyramid_bimt.scripts.populate import add_groups
from pyramid_bimt.scripts.populate import add_mailings
from pyramid_bimt.scripts.populate import add_users
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.tests.test_user_views import _make_user
from pyramid_mailer import get_mailer

import colander
import deform
import mock
import unittest


def _make_group(
    id=1,
    name='foo',
    users=None,
):
    if users is None:
        users = [_make_user()]
    return Group(
        id=id,
        name=name,
        users=users,
    )


def _make_mailing(
    id=1,
    name='foo',
    groups=None,
    exclude_groups=None,
    trigger=MailingTriggers.never.name,
    days=0,
    subject=u'Sübject',
    body=u'Bödy',
):
    if groups is None:
        groups = [_make_group()]
    if exclude_groups is None:
        exclude_groups = []
    return Mailing(
        id=id,
        name=name,
        groups=groups,
        exclude_groups=exclude_groups,
        trigger=trigger,
        days=days,
        subject=subject,
        body=body,
    )


class TestMailingList(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        from pyramid_bimt.views.mailing import MailingView
        self.context = testing.DummyResource()
        self.request = testing.DummyRequest(layout_manager=mock.Mock())
        self.view = MailingView(self.context, self.request)

    def tearDown(self):
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.mailing.Mailing')
    @mock.patch('pyramid_bimt.views.mailing.app_assets')
    @mock.patch('pyramid_bimt.views.mailing.table_assets')
    def test_view_setup(self, table_assets, app_assets, Mailing):
        Mailing.query.order_by.return_value.all.return_value = []
        self.view.__init__(self.context, self.request)
        self.view.list()

        self.assertTrue(self.request.layout_manager.layout.hide_sidebar)
        app_assets.need.assert_called_with()
        table_assets.need.assert_called_with()

    @mock.patch('pyramid_bimt.views.mailing.Mailing')
    def test_result(self, Mailing):
        mailing = _make_mailing()
        Mailing.query.order_by.return_value.all.return_value = [mailing, ]
        result = self.view.list()

        self.assertEqual(result, {
            'triggers': MailingTriggers,
            'mailings': [mailing, ],
        })


class TestMailingAdd(unittest.TestCase):

    APPSTRUCT = {
        'name': 'foo',
        'groups': [1, ],
        'exclude_groups': [2, ],
        'trigger': 'never',
        'days': 30,
        'subject': u'Foö',
        'body': u'Bär',
    }

    def setUp(self):
        self.config = testing.setUp()
        add_routes_mailing(self.config)
        initTestingDB(groups=True)

        from pyramid_bimt.views.mailing import MailingAdd
        self.request = testing.DummyRequest()
        self.view = MailingAdd(self.request)

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
        self.assertEqual(result.location, '/mailing/1/edit')

        mailing = Mailing.by_id(1)
        self.assertEqual(mailing.name, 'foo')
        self.assertEqual(mailing.groups, [Group.by_id(1)])
        self.assertEqual(mailing.exclude_groups, [Group.by_id(2)])
        self.assertEqual(mailing.trigger, MailingTriggers.never.name)
        self.assertEqual(mailing.days, 30)
        self.assertEqual(mailing.subject, u'Foö')
        self.assertEqual(mailing.body, u'Bär')

        self.assertEqual(
            self.request.session.pop_flash(), [u'Mailing "foo" added.'])


class TestMailingEdit(unittest.TestCase):

    APPSTRUCT = {
        'name': 'bar',
        'groups': [1, 2],
        'exclude_groups': [3, ],
        'trigger': 'after_created',
        'days': 7,
        'subject': u'Bär',
        'body': u'Bän',
    }

    def setUp(self):
        settings = {
            'mail.default_sender': 'admin@bimt.com',
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        initTestingDB(groups=True, mailings=True)
        add_routes_mailing(self.config)

        from pyramid_bimt.views.mailing import MailingEdit
        self.request = testing.DummyRequest()
        self.view = MailingEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_appstruct_empty_context(self):
        self.request.context = Mailing()
        self.assertEqual(self.view.appstruct(), {})

    def test_appstruct_full_context(self):
        self.request.context = Mailing.by_id(1)
        self.assertEqual(self.view.appstruct(), {
            'name': 'welcome_email',
            'groups': ['3', ],
            'exclude_groups': ['1', ],
            'trigger': MailingTriggers.after_created.name,
            'days': 1,
            'subject': u'Über Welcome!',
            'body': u'Welcome to this über amazing BIMT app!',
        })

    def test_save_success(self):
        self.request.context = Mailing.by_id(1)

        result = self.view.save_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/mailing/1/edit')

        mailing = Mailing.by_id(1)
        self.assertEqual(mailing.name, 'bar')
        self.assertEqual(mailing.groups, [Group.by_id(1), Group.by_id(2)])
        self.assertEqual(mailing.exclude_groups, [Group.by_id(3)])
        self.assertEqual(mailing.trigger, MailingTriggers.after_created.name)
        self.assertEqual(mailing.days, 7)
        self.assertEqual(mailing.subject, u'Bär')
        self.assertEqual(mailing.body, u'Bän')
        self.assertEqual(
            self.request.session.pop_flash(), [u'Mailing "bar" modified.'])

    def test_test_success(self):
        add_users()
        self.request.user = User.by_id(1)
        self.request.context = Mailing.by_id(1)

        result = self.view.test_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/mailing/1/edit')

        self.assertEqual(
            self.request.session.pop_flash(),
            [u'Mailing "welcome_email" sent to "admin@bar.com".'],
        )

        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject, u'[Mailing Test] Über Welcome!')
        self.assertIn('This mailing would be sent to:', mailer.outbox[0].html)
        self.assertIn('one@bar.com', mailer.outbox[0].html)

    def test_test_success_non_unicode(self):
        add_users()
        self.request.user = User.by_id(1)
        self.request.context = _make_mailing(
            id=1,
            name='foo',
            groups=None,
            exclude_groups=None,
            trigger=MailingTriggers.never.name,
            days=0,
            subject='Subject',
            body='Body',
        )

        with self.assertRaises(AssertionError) as cm:
            self.view.test_success(self.APPSTRUCT)
        self.assertEqual(
            cm.exception.message,
            'Mail body type must be unicode, not <type \'str\'>!'
        )

    @mock.patch('pyramid_bimt.models.get_current_request')
    def test_send_immediately_success(self, get_current_request):
        get_current_request.return_value = self.request
        add_users()
        self.request.context = Mailing.by_id(1)

        result = self.view.send_immediately_success(self.APPSTRUCT)
        self.assertIsInstance(result, HTTPFound)
        self.assertEqual(result.location, '/mailing/1/edit')

        self.assertEqual(
            self.request.session.pop_flash(),
            [u'Mailing "welcome_email" sent to 1 recipients.'],
        )

        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].recipients, ['one@bar.com', ])
        self.assertEqual(mailer.outbox[0].subject, u'Über Welcome!')

        self.assertIn(
            u'Hello Öne Bar', mailer.outbox[0].html,)
        self.assertIn(
            u'Welcome to this über amazing BIMT app!', mailer.outbox[0].html)
        self.assertIn('Best wishes,', mailer.outbox[0].html)
        self.assertIn('BIMT Team', mailer.outbox[0].html)

    @mock.patch('pyramid_bimt.models.get_current_request')
    def test_send_immediately_success_non_unicode(self, get_current_request):
        get_current_request.return_value = self.request
        add_users()
        self.request.context = _make_mailing(
            id=1,
            name='foo',
            groups=None,
            exclude_groups=None,
            trigger=MailingTriggers.never.name,
            days=0,
            subject='Subject',
            body='Body',
        )

        with self.assertRaises(AssertionError) as cm:
            self.view.send_immediately_success(self.APPSTRUCT)
        self.assertEqual(
            cm.exception.message,
            'Mail body type must be unicode, not <type \'str\'>!'
        )


class TestMailUnsubscribe(unittest.TestCase):

    def setUp(self):
        settings = {
            'mail.default_sender': 'admin@bimt.com',
            'bimt.app_title': 'BIMT',
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('pyramid_mailer.testing')
        initTestingDB(groups=True, mailings=True, users=True)
        add_routes_mailing(self.config)

        from pyramid_bimt.views.mailing import MailingEdit
        self.request = testing.DummyRequest()
        self.view = MailingEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.models.get_current_request')
    def test_in_unsubscribed(self, get_current_request):
        get_current_request.return_value = self.request
        add_routes_user(self.config)
        self.request.user = User.by_id(1)
        self.request.context = _make_mailing(
            id=123, name='excluded',
            groups=[Group.by_name('admins'), Group.by_name('enabled')],
            exclude_groups=[Group.by_name('unsubscribed')],
            body=u'Body', subject=u'Subject'
        )

        mailer = get_mailer(self.request)

        self.request.context.send(self.request.user)

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject, u'Subject')
        self.assertIn('<a href="http://example.com/unsubscribe">Unsubscribe from our Newsletter</a>', mailer.outbox[0].html)  # noqa

    @mock.patch('pyramid_bimt.models.get_current_request')
    def test_not_in_unsubscribed(self, get_current_request):
        get_current_request.return_value = self.request
        add_routes_user(self.config)
        self.request.user = User.by_id(1)
        self.request.context = _make_mailing(
            id=123, name='excluded',
            groups=[Group.by_name('admins'), Group.by_name('enabled')],
            exclude_groups=[],
            body=u'Body', subject=u'Subject'
        )

        mailer = get_mailer(self.request)

        self.request.context.send(self.request.user)

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject, u'Subject')
        self.assertNotIn('Unsubscribe from our Newsletter', mailer.outbox[0].html)  # noqa


class TestBefore(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

        from pyramid_bimt.views.mailing import MailingEdit
        self.request = testing.DummyRequest()
        self.view = MailingEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_buttons(self):
        schema = colander.Schema()
        form = deform.Form(schema, buttons=[])
        self.view.before(form)
        self.assertEqual(
            form.buttons,
            [],
        )

    def test_no_send_immediately_button(self):
        schema = colander.Schema()
        form = deform.Form(schema, buttons=['foo', 'bar'])
        self.view.before(form)
        self.assertEqual(form.buttons[0].value, 'foo')
        self.assertEqual(form.buttons[1].value, 'bar')

    def test_set_value_for_send_immediately_button(self):
        add_groups()
        add_users()
        add_mailings()
        self.request.context = Mailing.by_id(1)

        schema = colander.Schema()
        form = deform.Form(schema, buttons=['foo', 'bar', 'send_immediately'])
        self.view.before(form)
        self.assertEqual(form.buttons[0].value, 'foo')
        self.assertEqual(form.buttons[1].value, 'bar')
        self.assertEqual(
            form.buttons[2].value,
            'Immediately send mailing "welcome_email" to all 1 recipients '
            'without date constraints?'
        )


class TestRecipients(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        initTestingDB()

        from pyramid_bimt.views.mailing import MailingEdit
        self.request = testing.DummyRequest()
        self.view = MailingEdit(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_no_groups(self):
        mailing = _make_mailing(name='foo', groups=[])
        self.request.context = mailing

        self.assertEqual(
            self.view.recipients,
            set([]),
        )

    def test_no_groups_members(self):
        group = _make_group(name='foo', users=[])
        mailing = _make_mailing(name='foo', groups=[group, ])
        self.request.context = mailing

        self.assertEqual(
            self.view.recipients,
            set([]),
        )

    def test_union(self):
        add_groups()
        add_users()
        mailing = _make_mailing(
            name='foo',
            groups=[Group.by_name('admins'), Group.by_name('enabled')],
        )
        self.request.context = mailing

        self.assertItemsEqual(
            self.view.recipients,
            [User.by_email('admin@bar.com'), User.by_email('one@bar.com')],
        )

    def test_exclude(self):
        add_groups()
        add_users()
        mailing = _make_mailing(
            name='foo',
            groups=[Group.by_name('admins'), Group.by_name('enabled')],
            exclude_groups=[Group.by_name('admins')],
        )
        self.request.context = mailing

        self.assertItemsEqual(
            self.view.recipients,
            [User.by_email('one@bar.com')],
        )
