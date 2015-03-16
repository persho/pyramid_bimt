# -*- coding: utf-8 -*-
"""Settings view that should be extended by apps."""
from deform.form import Button
from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid_bimt.clickbank import ClickbankAPI
from pyramid_bimt.clickbank import ClickbankException
from pyramid_bimt.events import IUserCreated
from pyramid_bimt.events import UserSubscriptionChangeFailed
from pyramid_bimt.events import UserSubscriptionChanged
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.security import generate
from pyramid_bimt.views import FormView
from pyramid_deform import CSRFSchema

import colander
import deform
import logging
import re

logger = logging.getLogger(__name__)


# Apps can use this validator for their settings views
@colander.deferred
def deferred_settings_email_validator(node, kw):
    """Validator for setting email in settings, checks for email duplicates"""
    request = kw['request']

    def validator(node, cstruct):
        colander.Email()(node, cstruct)
        if request.user.email != cstruct and User.by_email(cstruct):
            raise colander.Invalid(
                node,
                u'Email {} is already in use by another user.'.format(cstruct)
            )
    return validator


class AccountInformation(colander.MappingSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=deferred_settings_email_validator,
    )

    fullname = colander.SchemaNode(
        colander.String(),
        missing='',
        title='Full Name',
        validator=colander.Range(50),
    )

    api_key = colander.SchemaNode(
        colander.String(),
        missing='',
        title='API key',
        widget=deform.widget.TextInputWidget(
            template='readonly/textinput'
        )
    )


@colander.deferred
def deferred_subscription_widget(node, kw):
    request = kw.get('request')
    return deform.widget.MappingWidget(
        product_group=request.user.product_group,
        template='subscription_mapping'
    )


@colander.deferred
def deferred_affiliate_widget(node, kw):
    request = kw.get('request')
    return deform.widget.TextInputWidget(
        referral_url=request.registry.settings['bimt.referral_url'],
        template='clickbank_affiliate_id.pt'
    )


@colander.deferred
def deferred_upgrade_group_choices_widget(node, kw):
    request = kw.get('request')
    if request.user.product_group and request.user.product_group.upgrade_groups:  # noqa
        choices = [(g.id, g.name) for
                   g in request.user.product_group.upgrade_groups]
    else:
        choices = []
    return deform.widget.SelectWidget(
        values=choices,
        template='upgrade_select'
    )


class UpgradeDowngradeSubscription(colander.MappingSchema):

    upgrade_subscription = colander.SchemaNode(
        colander.String(),
        missing='',
        title='Upgrade Subscription',
        widget=deferred_upgrade_group_choices_widget
    )

    downgrade_subscription = colander.SchemaNode(
        colander.String(),
        missing='',
        default=('For downgrading your subscription, please contact us '
                 ' at support@easyblognetworks.com'),
        title='Downgrade Subscription',
        widget=deform.widget.TextInputWidget(
            template='readonly/textinput'
        )
    )


class AffiliateSchema(colander.MappingSchema):
    clickbank_affiliate_id = colander.SchemaNode(
        colander.String(),
        missing=u'',
        title='Clickbank Affiliate ID',
        validator=colander.Range(50),
        widget=deferred_affiliate_widget,
    )


class SettingsSchema(CSRFSchema, colander.MappingSchema):
    account_info = AccountInformation(title='Account Information')
    change_subscription = UpgradeDowngradeSubscription(
        title='Change Subscription',
        widget=deferred_subscription_widget,
    )
    affiliate_settings = AffiliateSchema(title='Affiliate Settings')


class SettingsForm(FormView):
    schema = SettingsSchema()
    title = 'Settings'
    form_options = (('formid', 'settings'), ('method', 'POST'))

    def __init__(self, request):
        super(SettingsForm, self).__init__(request)
        # Don't allow upgrading to trial users and users without product group
        if ((not request.user.product_group or request.user.trial) and
                self.schema.get('change_subscription')):
            self.schema = self.schema.clone()
            self.schema.__delitem__('change_subscription')

    def __call__(self):
        self.buttons = (
            'save',
            Button(name='regenerate_api_key', title='Regenerate API key'),
            Button(name='upgrade_subscription', css_class='hidden'),
        )
        if self.request.user.unsubscribed:
            subscribe_button = Button(
                name='subscribe_to_newsletter',
                title='Subscribe to newsletter'
            )
            self.buttons = self.buttons + (subscribe_button, )
        return super(SettingsForm, self).__call__()

    def save_success(self, appstruct):
        user = self.request.user
        headers = None
        # if email was modified, we need to re-set the user's session
        email = appstruct['account_info']['email'].lower()
        if user.email != email:
            user.email = email
            headers = remember(self.request, user.email)
        user.fullname = appstruct['account_info']['fullname']
        self.request.user.set_property(
            'clickbank_affiliate_id',
            appstruct['affiliate_settings']['clickbank_affiliate_id'],
        )
        self.request.session.flash(u'Your changes have been saved.')
        return HTTPFound(location=self.request.path_url, headers=headers)

    def regenerate_api_key_success(self, appstruct):
        self.request.user.set_property(
            'api_key', generate_api_key(), secure=True)
        self.request.session.flash(u'API key re-generated.')

    def upgrade_subscription_success(self, appstruct):
        old_group = self.request.user.product_group
        new_group = Group.by_id(
            appstruct['change_subscription']['upgrade_subscription'])

        try:
            receipt = self._change_clickbank_subscription(new_group)
        except ClickbankException as exc:
            comment = (
                u'Your upgrade has not completed successfully. Support team '
                'has been notified and they are looking into the problem.')
            self.request.session.flash(comment)
            self.request.registry.notify(
                UserSubscriptionChangeFailed(
                    self.request,
                    self.request.user,
                    comment=comment
                )
            )
            logger.exception(exc)
            return HTTPFound(location=self.request.path_url)

        self.request.user.groups.remove(old_group)
        self.request.user.groups.append(new_group)
        comment = (
            u'Your subscription ({}) has been upgraded '
            'from {} to {}.'.format(receipt, old_group.name, new_group.name)
        )
        self.request.user.set_property('upgrade_completed', True)
        self.request.session.flash(comment)
        self.request.registry.notify(
            UserSubscriptionChanged(
                self.request,
                self.request.user,
                comment=comment
            )
        )
        return HTTPFound(location=self.request.path_url)

    def subscribe_to_newsletter_success(self, appstruct):
        self.request.session.flash(
            u'You have been subscribed to newsletter.')
        self.request.user.subscribe()
        return HTTPFound(location=self.request.path_url)

    def appstruct(self):
        user = self.request.user
        return {
            'account_info': {
                'email': user.email,
                'fullname': user.fullname,
                'api_key': user.get_property('api_key', '', secure=True),
            },
            'affiliate_settings': {
                'clickbank_affiliate_id': user.get_property(
                    'clickbank_affiliate_id', '')
            }
        }

    def _change_clickbank_subscription(self, new_group):
        clickbank_client = ClickbankAPI(
            self.request.registry.settings['bimt.clickbank_dev_key'],
            self.request.registry.settings['bimt.clickbank_api_key'],
        )
        return clickbank_client.change_user_subscription(
            self.request.user.email,
            self.request.user.product_group.product_id,
            new_group.product_id
        )


def generate_api_key():
    return re.sub(
        r'(....)(....)(....)(....)', r'\1-\2-\3-\4', unicode(generate(size=16))
    )


@subscriber(IUserCreated)
def set_api_key(event):
    event.user.set_property('api_key', generate_api_key(), secure=True)
