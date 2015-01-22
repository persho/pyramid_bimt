# -*- coding: utf-8 -*-
"""Tests for settings view."""

from pyramid import testing
from pyramid.threadlocal import get_current_request
from pyramid_basemodel import Session
from pyramid_bimt import configure
from pyramid_bimt.models import User
from pyramid_bimt.testing import initTestingDB
from pyramid_bimt.views.settings import SettingsForm


import mock
import unittest


class TestSettingsView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(request=testing.DummyRequest())
        configure(self.config)
        self.request = get_current_request()
        self.request.user = mock.Mock(product_group=None)

        from pyramid_layout.layout import LayoutManager

        self.request.layout_manager = LayoutManager('context', 'requestr')

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_settings_view(self):
        request = testing.DummyRequest()
        request.context = mock.Mock()
        resp = SettingsForm(request)
        self.assertEqual(resp.title, 'Settings')

    def test_view_csrf_token(self):
        settings_view = SettingsForm(self.request)
        csrf_token_field = settings_view.schema.get('csrf_token')
        self.assertIsNotNone(csrf_token_field)
        self.assertEqual(csrf_token_field.title, 'Csrf Token')

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_settings_view_response(self, find_layout):

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        find_layout.return_value = mock.Mock(spec='current_page')

        settings_view = SettingsForm(self.request)
        self.assertEqual(type(settings_view), SettingsForm)
        resp = settings_view()
        self.assertEqual('Settings', resp['title'])

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_settings_view_save_success(self, find_layout):

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        self.request.user.email = 'one@bar.com'
        self.request.user.fullname = 'John'
        form_values = {
            'account_info': {'email': 'TWO@bar.com', 'fullname': 'James'},
        }
        settings_view = SettingsForm(self.request)
        settings_view.save_success(form_values)
        self.assertEqual(self.request.user.email, 'two@bar.com')
        self.assertEqual(self.request.user.fullname, 'James')
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your changes have been saved.'],
        )

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_settings_view_save_success_same_email(self, find_layout):

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        self.request.user.email = 'one@bar.com'
        self.request.user.fullname = 'John'
        form_values = {
            'account_info': {'email': 'one@bar.com', 'fullname': 'John'},
        }
        settings_view = SettingsForm(self.request)
        settings_view.save_success(form_values)
        self.assertEqual(self.request.user.email, 'one@bar.com')
        self.assertEqual(self.request.user.fullname, 'John')
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your changes have been saved.'],
        )

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_regenerate_api_key_success(self, find_layout):

        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)
        req = get_current_request()
        req.user = mock.Mock()
        settings_view = SettingsForm(req)
        settings_view.regenerate_api_key_success(None)
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'API key re-generated.'],
        )


class TestGenerateAPIKeyOnUserCreation(unittest.TestCase):

    def setUp(self):
        settings = {
            'bimt.encryption_aes_16b_key': 'abcdabcdabcdabcd',
        }
        self.config = testing.setUp(settings=settings)
        initTestingDB(groups=True, users=True, auditlog_types=True)
        configure(self.config)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_bimt.views.settings.generate')
    def test_api_key_set_on_user_creation(self, mocked_generate):
        mocked_generate.return_value = 'foo'

        from pyramid_bimt.events import UserCreated

        user = User(email='foo@bar.com')
        Session.add(user)

        request = testing.DummyRequest()
        request.registry.notify(UserCreated(request, user, u'foö'))

        self.assertEqual(user.get_property('api_key', secure=True), u'foo')

    def test_generate_api_key(self):
        from pyramid_bimt.views.settings import generate_api_key
        import re

        api_key = generate_api_key()

        self.assertEqual(type(api_key), unicode)
        self.assertIsNotNone(re.match(r'(....)-(....)-(....)-(....)', api_key))


class TestSubscription(unittest.TestCase):

    def setUp(self):
        initTestingDB(groups=True, users=True)
        self.config = testing.setUp()
        self.request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            user=User.by_id(2),
        )
        self.view = SettingsForm(self.request)

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_subscribe_to_newsletter_button_missing(self, find_layout):
        response = self.view()
        self.assertNotIn('Subscribe to newsletter', response['form'])

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_subscribe_to_newsletter_button_present(self, find_layout):
        self.request.user.unsubscribe()
        response = self.view()
        self.assertIn('Subscribe to newsletter', response['form'])

    @mock.patch('pyramid_layout.layout.find_layout')
    def test_subscribe_to_newsletter_unsubscribed(self, find_layout):
        self.request.user.unsubscribe()
        self.view.subscribe_to_newsletter_success(None)
        self.assertEqual(
            self.request.session['_f_'],
            [u'You have been subscribed to newsletter.'],
        )
        self.assertFalse(self.request.user.unsubscribed)


class TestSettingsEmailValidator(unittest.TestCase):

    def setUp(self):
        from pyramid_bimt.testing import initTestingDB
        from pyramid_bimt.models import User

        self.config = testing.setUp()
        initTestingDB(groups=True, users=True)

        self.request = testing.DummyRequest(user=User.by_email('one@bar.com'))

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_valid_same_email(self):
        from pyramid_bimt.views.settings import deferred_settings_email_validator  # noqa

        cstruct = 'one@bar.com'

        validator = deferred_settings_email_validator(
            None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_valid_different_email(self):
        from pyramid_bimt.views.settings import deferred_settings_email_validator  # noqa

        cstruct = 'test@bar.com'

        validator = deferred_settings_email_validator(
            None, {'request': self.request})
        self.assertFalse(validator(None, cstruct))

    def test_invalid_email(self):
        from pyramid_bimt.views.settings import deferred_settings_email_validator  # noqa
        from colander import Invalid

        cstruct = 'fooooooo'

        validator = deferred_settings_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(cm.exception.msg, u'Invalid email address')

    def test_duplicate_email(self):
        from pyramid_bimt.views.settings import deferred_settings_email_validator  # noqa
        from colander import Invalid

        cstruct = 'admin@bar.com'

        validator = deferred_settings_email_validator(
            None, {'request': self.request})
        with self.assertRaises(Invalid) as cm:
            validator(None, cstruct)
        self.assertEqual(
            cm.exception.msg,
            u'Email admin@bar.com is already in use by another user.'
        )


class TestDefferedSubscriptionWidget(unittest.TestCase):

    def test_widget(self):
        from pyramid_bimt.views.settings import deferred_subscription_widget
        group = mock.Mock(name='test_group')
        kw = mock.MagicMock()
        kw.get.return_value.user.trial = False
        kw.get.return_value.user.product_group = group
        widget = deferred_subscription_widget(None, kw)

        self.assertEqual(widget.product_group, group)
        self.assertEqual(widget.template, 'subscription_mapping')

    def test_widget_no_product_group(self):
        from pyramid_bimt.views.settings import deferred_subscription_widget
        from deform.widget import HiddenWidget
        kw = mock.MagicMock()
        kw.get.return_value.user.trial = False
        kw.get.return_value.user.product_group = None
        widget = deferred_subscription_widget(None, kw)

        self.assertEqual(type(widget), HiddenWidget)

    def test_widget_trial_user(self):
        from pyramid_bimt.views.settings import deferred_subscription_widget
        from deform.widget import HiddenWidget
        group = mock.Mock(name='test_group')
        kw = mock.MagicMock()
        kw.get.return_value.user.trial = True
        kw.get.return_value.user.product_group = group
        widget = deferred_subscription_widget(None, kw)

        self.assertEqual(type(widget), HiddenWidget)


class TestUpgradeGroupsChoicesWidget(unittest.TestCase):

    def setUp(self):
        from pyramid_bimt.views.settings import deferred_upgrade_group_choices_widget  # noqa
        self.widget = deferred_upgrade_group_choices_widget

    def test_present_choices_widget(self):
        from pyramid_bimt.models import Group
        groups = [Group(id=1, name='one'), Group(id=2, name='two')]

        group = mock.Mock(name='test_group', product_id=1)
        group.upgrade_groups = groups
        kw = mock.MagicMock()
        kw.get.return_value.user.product_group = group
        widget = self.widget(None, kw)

        self.assertEqual(widget.values[0], (groups[0].id, groups[0].name))
        self.assertEqual(widget.values[1], (groups[1].id, groups[1].name))
        self.assertEqual(widget.template, 'upgrade_select')

    def test_no_product_group_widget(self):
        kw = mock.MagicMock()
        kw.get.return_value.user.product_group = None
        widget = self.widget(None, kw)

        self.assertEqual(widget.values, [])
        self.assertEqual(widget.template, 'readonly/select')

    def test_no_choices_widget(self):
        groups = []

        group = mock.Mock(name='test_group', product_id=1)
        group.upgrade_groups = groups
        kw = mock.MagicMock()
        kw.get.return_value.user.product_group = group
        widget = self.widget(None, kw)

        self.assertEqual(widget.values, [])
        self.assertEqual(widget.template, 'readonly/select')


class TestDowngradeGroupsChoicesWidget(unittest.TestCase):

    def setUp(self):
        from pyramid_bimt.views.settings import deferred_downgrade_group_choices_widget  # noqa
        self.widget = deferred_downgrade_group_choices_widget

    def test_present_choices_widget(self):
        from pyramid_bimt.models import Group
        groups = [Group(id=1, name='one'), Group(id=2, name='two')]

        group = mock.Mock(name='test_group', product_id=1)
        group.downgrade_groups = groups
        kw = mock.MagicMock()
        kw.get.return_value.user.product_group = group
        widget = self.widget(None, kw)

        self.assertEqual(widget.values[0], (groups[0].id, groups[0].name))
        self.assertEqual(widget.values[1], (groups[1].id, groups[1].name))
        self.assertEqual(widget.template, 'downgrade_select')

    def test_no_product_group_widget(self):
        kw = mock.MagicMock()
        kw.get.return_value.user.product_group = None
        widget = self.widget(None, kw)

        self.assertEqual(widget.values, [])
        self.assertEqual(widget.template, 'readonly/select')

    def test_no_choices_widget(self):
        groups = []

        group = mock.Mock(name='test_group', product_id=1)
        group.downgrade_groups = groups
        kw = mock.MagicMock()
        kw.get.return_value.user.product_group = group
        widget = self.widget(None, kw)

        self.assertEqual(widget.values, [])
        self.assertEqual(widget.template, 'readonly/select')


@mock.patch.object(SettingsForm, '_change_clickbank_subscription')
@mock.patch('pyramid_layout.layout.find_layout')
class TestUpgradeDowngradeSubscription(unittest.TestCase):

    def setUp(self):
        from pyramid_bimt.tests.test_group_model import _make_group
        initTestingDB(groups=True, users=True, auditlog_types=True)
        self.config = testing.setUp(request=testing.DummyRequest())
        configure(self.config)
        self.request = get_current_request()
        self.request.user = User.by_id(1)
        self.group1 = _make_group(name='group1', product_id='1')
        self.group2 = _make_group(name='group2', product_id='2')
        self.request.user.groups = [self.group1, ]

        from pyramid_layout.layout import LayoutManager

        self.request.layout_manager = LayoutManager('context', 'requestr')

    def tearDown(self):
        Session.remove()
        testing.tearDown()

    def test_upgrade_subscription_success(
            self, find_layout, _change_clickbank_subscription):
        _change_clickbank_subscription.return_value = 1

        settings_view = SettingsForm(self.request)
        settings_view.upgrade_subscription_success(
            {'change_subscription': {'upgrade_subscription': self.group2.id}})
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your subscription (1) has been upgraded from group1 to group2.'],  # noqa
        )

        from pyramid_bimt.models import AuditLogEntry
        entry = AuditLogEntry.get_all(security=False).first()
        self.assertEqual(
            entry.comment,
            u'Your subscription (1) has been upgraded from group1 to group2.'
        )
        self.assertEqual(entry.user.id, self.request.user.id)

    def test_upgrade_subscription_exception(
            self, find_layout, _change_clickbank_subscription):
        from pyramid_bimt.clickbank import ClickbankException

        _change_clickbank_subscription.side_effect = ClickbankException()

        settings_view = SettingsForm(self.request)
        settings_view.upgrade_subscription_success(
            {'change_subscription': {'upgrade_subscription': self.group2.id}})
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your upgrade has not completed successfully. Support team has been notified and they are looking into the problem.'],  # noqa
        )

        from pyramid_bimt.models import AuditLogEntry
        entry = AuditLogEntry.get_all(security=False).first()
        self.assertEqual(
            entry.comment,
            u'Your upgrade has not completed successfully. Support team has been notified and they are looking into the problem.'  # noqa
        )
        self.assertEqual(entry.user.id, self.request.user.id)

    def test_downgrade_subscription_success(
            self, find_layout, _change_clickbank_subscription):

        _change_clickbank_subscription.return_value = 1
        self.config.testing_securitypolicy(
            userid='one@bar.com', permissive=True)

        settings_view = SettingsForm(self.request)
        settings_view.downgrade_subscription_success(
            {'change_subscription':
                {'downgrade_subscription': self.group2.id}})
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your subscription (1) has been downgraded from group1 to group2.'],  # noqa
        )

        from pyramid_bimt.models import AuditLogEntry
        entry = AuditLogEntry.get_all(security=False).first()
        self.assertEqual(
            entry.comment,
            u'Your subscription (1) has been downgraded from group1 to group2.'
        )
        self.assertEqual(entry.user.id, self.request.user.id)

    def test_downgrade_subscription_exception(
            self, find_layout, _change_clickbank_subscription):
        from pyramid_bimt.clickbank import ClickbankException

        _change_clickbank_subscription.side_effect = ClickbankException()

        settings_view = SettingsForm(self.request)
        settings_view.downgrade_subscription_success(
            {'change_subscription':
                {'downgrade_subscription': self.group2.id}})
        self.assertEqual(
            settings_view.request.session['_f_'],
            [u'Your downgrade has not completed successfully. Support team has been notified and they are looking into the problem.'],  # noqa
        )

        from pyramid_bimt.models import AuditLogEntry
        entry = AuditLogEntry.get_all(security=False).first()
        self.assertEqual(
            entry.comment,
            u'Your downgrade has not completed successfully. Support team has been notified and they are looking into the problem.'  # noqa
        )
        self.assertEqual(entry.user.id, self.request.user.id)


@mock.patch('pyramid_bimt.views.settings.ClickbankAPI')
class TestChangeSubscription(unittest.TestCase):

    def setUp(self):
        self.request = mock.Mock()
        self.request.registry.settings = {
            'bimt.clickbank_dev_key': 'secret',
            'bimt.clickbank_api_key': 'secret'
        }
        self.view = SettingsForm(self.request)

    def test_success(self, ClickbankAPI):
        ClickbankAPI.return_value.change_user_subscription.return_value = '111'
        self.assertEqual(
            self.view._change_clickbank_subscription(mock.Mock(product_id=1)),
            '111',
        )

    def test_exception(self, ClickbankAPI):
        from pyramid_bimt.clickbank import ClickbankException
        ClickbankAPI.return_value.change_user_subscription.side_effect = ClickbankException()  # noqa
        with self.assertRaises(ClickbankException):
            self.view._change_clickbank_subscription(mock.Mock(product_id=1))
