# -*- coding: utf-8 -*-
"""Integration with JVZoo & Clickbank Instant Payment Notification service."""

from Crypto.Cipher import AES
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

    def _parse_request_jvzoo(self):
        """Verify if received POST is a valid JVZoo POST request and save
        values to self.params.
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
            self.request.decrypted = __flatten__(json.loads(decrypted_str))
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


def __flatten__(d):
    def items():
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subvalue in __flatten__(value).items():
                    yield key + '.' + subkey, subvalue
            if isinstance(value, list):
                for index, item in enumerate(value):
                    for subkey, subvalue in __flatten__(item).items():
                        yield key + '.{}.'.format(index) + subkey, subvalue
            else:
                yield key, value

    return dict(items())
