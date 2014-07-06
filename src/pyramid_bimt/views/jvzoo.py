# -*- coding: utf-8 -*-
"""Integration with JVZoo Notification Service."""

from datetime import date
from datetime import timedelta
from flufl.enum import Enum
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid_bimt.events import UserCreated
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.models import Group
from pyramid_bimt.models import Session
from pyramid_bimt.models import User
from pyramid_bimt.security import encrypt
from pyramid_bimt.security import generate

import hashlib
import logging
import requests

logger = logging.getLogger(__name__)


class UserActions(Enum):
    """Actions that can be performed on a User object."""
    enable = 'enable'
    disable = 'disable'


TYPES_TO_ACTIONS = {
    'SALE': UserActions.enable,   # first payment
    'BILL': UserActions.enable,   # regular recurring payments
    'RFND': UserActions.disable,  # refund
    'CGBK': UserActions.disable,  # charge-back
    'INSF': UserActions.disable,  # insufficient funds
}
"""Mapping from JVZoo Transaction Types to user actions."""


class JVZooView(object):

    def __init__(self, request):
        self.request = request

    @view_config(
        route_name='jvzoo',
        permission=NO_PERMISSION_REQUIRED,
        renderer='string',
    )
    def jvzoo(self):
        """The /jvzoo view, called by the JVZoo Notification Service."""

        # check for POST request
        if not self.request.POST:
            msg = 'No POST request.'
            logger.exception(msg)
            return msg

        logger.info(self.request.POST.items())
        try:
            self._verify_POST()
            # try to find an existing user using the ``ccustemail``
            email = self.request.POST['ccustemail'].lower()
            user = User.by_email(email)
            if not user:
                user = User.by_billing_email(email)

            self.comment = u'{} by JVZoo, transaction id: {}, type: {}, note: {}'  # noqa
            self.trans_id = self.request.POST.get('ctransreceipt', u'unknown')
            self.trans_type = self.request.POST['ctransaction']

            # create a new user if no existing user found
            if not user:
                password = generate()
                user = User(
                    email=email,
                    password=encrypt(password),
                    fullname=u'{}'.format(
                        self.request.POST['ccustname'].decode('utf-8')),
                    affiliate=u'{}'.format(
                        self.request.POST['ctransaffiliate'].decode('utf-8').lower()),  # noqa
                )
                Session.add(user)
                self.request.registry.notify(
                    UserCreated(self.request, user, password, self.comment.format(  # noqa
                        u'Created', self.trans_id, self.trans_type, '')))
                logger.info('JVZoo created new user: {}'.format(user.email))

            group = Group.by_product_id(
                int(self.request.POST['cproditem']))
            if not group:
                raise ValueError(
                    'Cannot find group with product_id "{}"'.format(
                        self.request.POST['cproditem']))

            # perform jvzoo transaction actions
            self.jvzoo_transaction(user, group)

            # send request with same parameters to the URL specified on group
            if group.forward_ipn_to_url:
                requests.post(
                    group.forward_ipn_to_url,
                    params=self.request.POST,
                )
                logger.info(
                    'Request re-sent to {}.',
                    group.forward_ipn_to_url
                )

            logger.info('JVZoo done.')
            return 'Done.'

        except Exception as ex:
            msg = 'POST handling failed: {}: {}'.format(
                ex.__class__.__name__, ex.message)
            logger.exception(msg)
            return msg

    def jvzoo_transaction(self, user, group):
        """
        Select correct jvzoo transaction and call its method

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group

        """
        if self.trans_type == 'SALE':
            self.jvzoo_sale_transaction(user, group)

        elif self.trans_type == 'BILL':
            self.jvzoo_bill_transaction(user, group)

        elif self.trans_type in ['RFND', 'CGBK', 'INSF']:
            self.jvzoo_disable_transaction(user, group)

        else:
            raise ValueError(
                u'Unknown Transaction Type: {}'.format(self.trans_type))

    def jvzoo_sale_transaction(self, user, group):
        """
        Make jvzoo sale transaction

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group

        """
        if group.trial_validity:
            trial = True
            validity = timedelta(days=group.trial_validity)
            user.groups.append(Group.by_name('trial'))
        else:
            trial = False
            validity = timedelta(days=group.validity)

        user.valid_to = date.today() + validity
        user.last_payment = date.today()
        user.groups.append(group)
        user.enable()

        msg = self.comment.format(
            u'Enabled', self.trans_id, self.trans_type, '{} until {}'.format(
                'trial' if trial else 'regular', user.valid_to))
        logger.info(msg)
        self.request.registry.notify(
            UserEnabled(self.request, user, msg))

    def jvzoo_bill_transaction(self, user, group):
        """
        Make jvzoo bill transaction

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group

        """
        user.valid_to = date.today() + timedelta(days=group.validity)
        user.last_payment = date.today()
        user.groups.append(group)
        user.groups.remove(Group.by_name('trial'))
        user.enable()

        msg = self.comment.format(
            u'Enabled', self.trans_id, self.trans_type, 'regular until {}'.format(  # noqa
                user.valid_to))
        logger.info(msg)
        self.request.registry.notify(
            UserEnabled(self.request, user, msg))

    def jvzoo_disable_transaction(self, user, group):
        """
        Make jvzoo disable transaction

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group

        """
        groups_comment = 'removed from groups: {}'.format(
            ', '.join([g.name for g in user.groups]))
        user.valid_to = date.today()
        user.groups = []

        logger.info('JVZoo disabled user: {}'.format(user.email))
        self.request.registry.notify(
            UserDisabled(self.request, user, self.comment.format(
                u'Disabled', self.trans_id, self.trans_type, groups_comment)))

    def _verify_POST(self):
        """Verifies if received POST is a valid JVZoo POST request.

        :return: True if verified, raise ValueError if verification failed.
        :rtype: bool
        """
        # concatenate POST parameters into a string
        strparams = u''
        for key, value in sorted(self.request.POST.items()):
            if key != 'cverify':
                strparams += value + '|'

        # secretkey must be last
        strparams += self.request.registry.settings['bimt.jvzoo_secret_key']

        # calculate SHA digest and compare to ``cverify`` value
        sha = hashlib.sha1(strparams.encode('utf-8')).hexdigest().upper()
        if self.request.POST['cverify'] == sha[:8]:
            return True
        else:
            raise ValueError('Checksum verification failed')
