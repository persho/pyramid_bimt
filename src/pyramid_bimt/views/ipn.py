# -*- coding: utf-8 -*-
"""Integration with JVZoo & Clickbank Instant Payment Notification service."""

from Crypto.Cipher import AES
from copy import deepcopy
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
from pyramid_bimt.utils import AttrDict
from pyramid_bimt.utils import flatten

import hashlib
import json
import logging
import requests
import string

logger = logging.getLogger(__name__)

COMMENT = u'{} by {}, transaction id: {}, type: {}, note: {}'

MAPPING_JVZOO = {
    'ccustname': 'fullname',
    'ccustemail': 'email',
    'cproditem': 'product_id',
    'ctransaction': 'trans_type',
    'ctransreceipt': 'trans_id',
    'ctransaffiliate': 'affiliate',
}
MAPPING_CLICKBANK = {
    'customer.billing.fullName': 'fullname',
    'customer.billing.email': 'email',
    'lineItems.0.itemNo': 'product_id',
    'transactionType': 'trans_type',
    'receipt': 'trans_id',
    'affiliate': 'affiliate',
}


class UserActions(Enum):
    """Actions that can be performed on a User object."""
    enable = 'enable'
    disable = 'disable'


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

        # check that we have some content to work with
        if not self.request.POST:
            raise ValueError('No POST request.')

        self._parse_request_jvzoo()
        return self.ipn()

    @view_config(
        route_name='clickbank',
        permission=NO_PERMISSION_REQUIRED,
        renderer='string',
    )
    def clickbank(self):
        """Set provider to 'clickbank' and call IPN handler."""
        self.provider = 'clickbank'
        # check that we have some content to work with
        try:
            self.request.json_body
        except Exception:
            raise ValueError('No JSON request.')

        self._parse_request_clickbank()
        return self.ipn()

    def ipn(self):
        """The main IPN handler, called by the IPN service."""
        # skip over to-be-ignored products
        if self.params.product_id in self.request.registry.settings.get(
           'bimt.products_to_ignore', '').split(','):
            logger.info(
                'The product is listed on the ignore list: {}'.format(
                    self.params.product_id))
            return 'Done.'

        # try to find an existing user with given email
        user = User.by_email(self.params.email)
        if not user:
            user = User.by_billing_email(self.params.email)

        # create a new user if no existing user found
        if not user:
            password = generate()
            user = User(
                email=self.params.email,
                billing_email=self.params.email,
                password=encrypt(password),
                fullname=u'{}'.format(self.params.fullname),
                affiliate=u'{}'.format(self.params.get('affiliate', '')),
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
        if self.params.trans_type in ['SALE', 'TEST_SALE', 'TEST']:
            self.ipn_sale_transaction(user, group)

        elif self.params.trans_type in ['BILL', 'TEST_BILL']:
            self.ipn_bill_transaction(user, group)

        elif self.params.trans_type in ['RFND', 'CGBK', 'TEST_RFND']:
            self.ipn_disable_transaction(user, group)

        # IPN that clickbank sends after upgrade. Log it and do nothing
        # as upgrade is already completed
        elif 'SUBSCRIPTION-CHG' in self.params.trans_type:
            logger.info(
                '{} finished correctly.'.format(self.params.trans_type))

        elif self.params.trans_type in [
            'CANCEL-REBILL', 'INSF', 'CANCEL-TEST-REBILL',
        ]:
            logger.info('Don\'t do anything, user will be disabled when it\'s '
                        'subscription runs out.')
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
        else:
            trial = False
            validity = timedelta(days=group.validity)
        valid_to = date.today() + validity

        if trial and not group.addon:
            user.groups.append(Group.by_name('trial'))

        if group.addon:
            user.set_property(
                'addon_{}_valid_to'.format(group.product_id), valid_to)
            user.set_property(
                'addon_{}_last_payment'.format(group.product_id), date.today())
            action = u'Addon "{}" enabled'.format(group.name)
        else:
            user.valid_to = valid_to
            user.last_payment = date.today()
            user.enable()
            action = u'Enabled'

        if group not in user.groups:  # pragma: no branch
            user.groups.append(group)

        comment = COMMENT.format(
            action,
            self.provider,
            self.params.trans_id,
            self.params.trans_type,
            '{} until {}'.format(
                'trial' if trial else 'regular', valid_to))
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
        validity = timedelta(days=group.validity)
        valid_to = date.today() + validity

        if group.addon:
            user.set_property(
                'addon_{}_valid_to'.format(group.product_id), valid_to)
            user.set_property(
                'addon_{}_last_payment'.format(group.product_id), date.today())
            action = u'Addon "{}" enabled'.format(group.name)
        else:
            user.valid_to = valid_to
            user.last_payment = date.today()
            user.enable()
            action = u'Enabled'

            if Group.by_name('trial') in user.groups:
                user.groups.remove(Group.by_name('trial'))

        if group not in user.groups:  # pragma: no branch
            user.groups.append(group)

        comment = COMMENT.format(
            action,
            self.provider,
            self.params.trans_id,
            self.params.trans_type,
            'regular until {}'.format(valid_to),
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
        # If user just completed an upgrade, refund is part of the upgrade
        # and should not disable user
        if user.get_property('upgrade_completed', False):
            user.set_property('upgrade_completed', False)
            return

        if group.addon:
            user.groups.remove(group)
            user.set_property(
                'addon_{}_valid_to'.format(group.product_id), date.today())
            action = u'Addon "{}" disabled'.format(group.name)
            removed_groups = [group, ]
        else:
            user.valid_to = date.today()
            removed_groups = deepcopy(user.groups)
            user.groups = []
            action = u'Disabled'

        comment = COMMENT.format(
            action,
            self.provider,
            self.params.trans_id,
            self.params.trans_type,
            'removed from groups: {}'.format(
                ', '.join([g.name for g in removed_groups])),
        )
        self.request.registry.notify(
            UserDisabled(self.request, user, comment))

    def _parse_request_jvzoo(self):
        """Verify if received POST is a valid JVZoo POST request.

        Save parsed values to self.params.
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
        if not self.request.POST['cverify'] == sha[:8]:
            raise ValueError('Checksum verification failed')

        # re-map values from POST to fit common naming conventions
        self.params = AttrDict()
        for key, value in self.request.POST.items():
            if key in MAPPING_JVZOO:
                self.params[MAPPING_JVZOO[key]] = value

        # convert to common form
        for key, value in self.params.items():
            if key in ['fullname', ]:
                self.params[key] = value.decode('utf-8')
            if key in ['email', 'affiliate']:
                self.params[key] = value.lower()

    def _parse_request_clickbank(self):
        """Decrypt JSON received from a Clickbank JSON request and save
        values to self.params.
        """
        # decrypt values
        iv = self.request.json_body['iv']
        encrypted_str = self.request.json_body['notification']
        sha1 = hashlib.sha1()
        sha1.update(
            self.request.registry.settings['bimt.clickbank_secret_key'])
        cipher = AES.new(
            sha1.hexdigest()[:32], AES.MODE_CBC, iv.decode('base64'))

        decrypted_str = cipher.decrypt(encrypted_str.decode('base64')).strip(
            '')
        decrypted_str = filter(lambda x: x in string.printable, decrypted_str)  # noqa
        decrypted_str = decrypted_str.strip(
            ' \x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f')

        try:
            self.request.decrypted = flatten(json.loads(decrypted_str))
        except ValueError as e:
            logger.exception(e)
            raise ValueError('Decryption failed: {}'.format(decrypted_str))

        # re-map values from POST to fit common naming conventions
        self.params = AttrDict()
        for key, value in self.request.decrypted.iteritems():
            if key in MAPPING_CLICKBANK:
                self.params[MAPPING_CLICKBANK[key]] = value

        # convert to common form
        for key, value in self.params.items():
            if key in ['fullname', ]:
                self.params[key] = value.decode('utf-8')
            if key in ['email', ]:
                self.params[key] = value.lower()
