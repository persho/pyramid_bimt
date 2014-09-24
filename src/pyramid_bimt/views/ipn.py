# -*- coding: utf-8 -*-
"""Integration with JVZoo & Clickbank Instant Payment Notification service."""

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

COMMENT = u'{} by {}, transaction id: {}, type: {}, note: {}'


class UserActions(Enum):
    """Actions that can be performed on a User object."""
    enable = 'enable'
    disable = 'disable'


class AttrDict(dict):
    """Dict with support for attribute access."""
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class IPNView(object):
    """Handle IPN POST requests to BIMT app."""

    provider = None  # 'jvzoo' or 'clickbank'

    def __init__(self, request):
        self.request = request

    @view_config(
        route_name='jvzoo',
        permission=NO_PERMISSION_REQUIRED,
        renderer='string',
    )
    def jvzoo(self):
        """Set provider to 'jvzoo' and call IPN handler."""
        self.provider = 'jvzoo'
        return self.ipn()

    @view_config(
        route_name='clickbank',
        permission=NO_PERMISSION_REQUIRED,
        renderer='string',
    )
    def clickbank(self):  # pragma: no cover
        """Set provider to 'clickbank' and call IPN handler."""
        self.provider = 'clickbank'
        return self.ipn()

    def ipn(self):
        """The main IPN handler, called by the IPN service."""

        # check for POST request
        if not self.request.POST:
            msg = 'No POST request.'
            logger.exception(msg)
            return msg

        logger.info(self.request.POST.items())
        self._verify_POST()
        self._map_POST()

        # try to find an existing user with given email
        user = User.by_email(self.params.email)
        if not user:
            user = User.by_billing_email(self.params.email)

        # create a new user if no existing user found
        if not user:
            password = generate()
            user = User(
                email=self.params.email,
                password=encrypt(password),
                fullname=u'{}'.format(self.params.fullname),
                affiliate=u'{}'.format(self.params.affiliate),
            )
            Session.add(user)

            comment = COMMENT.format(
                u'Created',
                self.provider,
                self.params.trans_id,
                self.params.trans_type,
                '',
            )
            logger.info(comment)
            self.request.registry.notify(
                UserCreated(self.request, user, password, comment))

        # find a group that is used for given product
        group = Group.by_product_id(self.params.product_id)
        if not group:
            raise ValueError(
                'Cannot find group with product_id "{}"'.format(
                    self.params.product_id))

        # perform IPN transaction actions
        self.ipn_transaction(user, group)

        # send request with same parameters to the URL specified on group
        if group.forward_ipn_to_url:
            requests.post(
                group.forward_ipn_to_url,
                params=self.request.POST,
            )
            logger.info(
                'IPN re-posted to {}.'.format(group.forward_ipn_to_url))

        logger.info('IPN done.')
        return 'Done.'

    def ipn_transaction(self, user, group):
        """Select correct IPN transaction type and call its method.

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group
        """
        if self.params.trans_type in ['SALE', 'TEST_SALE']:
            self.ipn_sale_transaction(user, group)

        elif self.params.trans_type in ['BILL', 'TEST_BILL']:
            self.ipn_bill_transaction(user, group)

        elif self.params.trans_type in ['RFND', 'CGBK', 'INSF', 'TEST_RFND']:
            self.ipn_disable_transaction(user, group)

        else:
            raise ValueError(
                u'Unknown Transaction Type: {}'.format(self.params.trans_type))

    def ipn_sale_transaction(self, user, group):
        """Handle IPN sale transaction.

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
        if group not in user.groups:  # pragma: no branch
            user.groups.append(group)
        user.enable()

        comment = COMMENT.format(
            u'Enabled',
            self.provider,
            self.params.trans_id,
            self.params.trans_type,
            '{} until {}'.format(
                'trial' if trial else 'regular', user.valid_to))
        logger.info(comment)
        self.request.registry.notify(
            UserEnabled(self.request, user, comment))

    def ipn_bill_transaction(self, user, group):
        """Handle IPN bill transaction.

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group
        """
        user.valid_to = date.today() + timedelta(days=group.validity)
        user.last_payment = date.today()
        user.groups.append(group)
        if Group.by_name('trial') in user.groups:
            user.groups.remove(Group.by_name('trial'))
        user.enable()

        comment = COMMENT.format(
            u'Enabled',
            self.provider,
            self.params.trans_id,
            self.params.trans_type,
            'regular until {}'.format(user.valid_to),
        )
        logger.info(comment)
        self.request.registry.notify(
            UserEnabled(self.request, user, comment))

    def ipn_disable_transaction(self, user, group):
        """Handle IPN disable transaction.

        :param    user:  Selected user
        :type     user:  pyramid_bimt.models.user.User
        :param    group: Group that user belongs to
        :type     group: pyramid_bimt.models.Groups.Group
        """
        groups_comment = 'removed from groups: {}'.format(
            ', '.join([g.name for g in user.groups]))
        user.valid_to = date.today()
        user.groups = []

        comment = COMMENT.format(
            u'Disabled',
            self.provider,
            self.params.trans_id,
            self.params.trans_type,
            groups_comment,
        )
        self.request.registry.notify(
            UserDisabled(self.request, user, comment))

    def _verify_POST(self):
        """Verifies if received POST is a valid IPN POST request.

        :return: True if verified, raise ValueError if verification failed.
        :rtype: bool
        """
        if self.provider == 'jvzoo':
            return self._verify_POST_jvzoo()
        elif self.provider == 'clickbank':
            return self._verify_POST_clickbank()
        else:
            raise ValueError('Unknown provider: {}'.format(self.provider))

    def _verify_POST_jvzoo(self):
        """Verifies if received POST is a valid JVZoo POST request.

        :return: True if verified, raise ValueError if verification failed.
        :rtype: bool
        """
        # concatenate POST parameters into a string
        strparams = u''
        for key, value in sorted(self.request.POST.items()):
            if key != 'cverify':
                strparams += str(value) + '|'

        # secretkey must be last
        strparams += self.request.registry.settings['bimt.jvzoo_secret_key']

        # calculate SHA digest and compare to ``cverify`` value
        sha = hashlib.sha1(strparams.encode('utf-8')).hexdigest().upper()
        if self.request.POST['cverify'] == sha[:8]:
            return True
        else:
            raise ValueError('Checksum verification failed')

    def _verify_POST_clickbank(self):  # pragma: no cover
        """Verifies if received POST is a valid Clickbank POST request.

        :return: True if verified, raise ValueError if verification failed.
        :rtype: bool
        """
        raise ValueError('ClickBank POST verification not yet implemented.')

    def _map_POST(self):
        """Remaps values from POST to fit common naming conventions."""
        MAPPING_JVZOO = {
            'ccustname': 'fullname',
            'ccustemail': 'email',
            'cproditem': 'product_id',
            'ctransaction': 'trans_type',
            'ctransreceipt': 'trans_id',
            'ctransaffiliate': 'affiliate',
        }
        MAPPING_CLICKBANK = {}
        if self.provider == 'jvzoo':
            MAPPING = MAPPING_JVZOO
        elif self.provider == 'clickbank':  # pragma: no cover
            MAPPING = MAPPING_CLICKBANK
        else:
            raise ValueError('Unknown provider: {}'.format(self.provider))

        self.params = AttrDict()
        for key, value in self.request.POST.iteritems():
            if key in MAPPING:
                self.params[MAPPING[key]] = value

        # convert to common form
        for key, value in self.params.items():
            if key in ['fullname', ]:
                self.params[key] = value.decode('utf-8')
            if key in ['email', 'affiliate']:
                self.params[key] = value.lower()
