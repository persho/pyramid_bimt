# -*- coding: utf-8 -*-
"""Integration with JVZoo Notification Service."""

from datetime import date
from datetime import timedelta
from flufl.enum import Enum
from pyramid.view import view_config
from pyramid_bimt.events import UserCreated
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.models import Session
from pyramid_bimt.models import User
from pyramid_bimt.security import encrypt
from pyramid_bimt.security import generate
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.renderers import render

import logging
import hashlib

logger = logging.getLogger(__name__)


class UserActions(Enum):
    """Actions that can be performed on a User object."""
    enable = 'enable'
    disable = 'disable'


TYPES_TO_ACTIONS = {
    'SALE': UserActions.enable,   # first payment, trial subscription
    'BILL': UserActions.enable,   # regular recurring payments
    'RFND': UserActions.disable,  # refund
    'CGBK': UserActions.disable,  # charge-back
    'INSF': UserActions.disable,  # insufficient funds
}
"""Mapping from JVZoo Transaction Types to user actions."""


class JVZooView(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='jvzoo')
    def jvzoo(self):
        """The /jvzoo view, called by the JVZoo Notification Service."""

        # check for POST request
        if not self.request.POST:
            msg = 'No POST request.'
            logger.warning(msg)
            return msg

        logger.info(self.request.POST.items())
        try:
            self._verify_POST()

            # try to find an existing user using the ``ccustemail``
            user = User.by_email(self.request.POST['ccustemail'])
            if not user:
                user = User.by_billing_email(self.request.POST['ccustemail'])

            comment = u'{} by JVZoo, transaction id: {}, type: {}'
            trans_id = self.request.POST.get('ctransreceipt', u'unknown')
            trans_type = self.request.POST['ctransaction']

            # create a new user if no existing user found
            if not user:
                password = generate()
                user = User(
                    email=self.request.POST['ccustemail'],
                    password=encrypt(password),
                    fullname=u'{}'.format(
                        self.request.POST['ccustname'].decode('utf-8')),
                    affiliate=u'{}'.format(
                        self.request.POST['ctransaffiliate'].decode('utf-8')),
                )
                Session.add(user)
                self.request.registry.notify(
                    UserCreated(self.request, user, comment.format(
                        u'Created', trans_id, trans_type)))
                self.send_welcome_email(user, password)

            # perform different actions for different transaction types
            if trans_type == 'SALE':
                validity = self.request.registry.settings[
                    'bimt.jvzoo_trial_period']
                user.valid_to = date.today() + timedelta(days=validity)
                user.enable()
                self.request.registry.notify(
                    UserEnabled(self.request, user, comment.format(
                        u'Enabled', trans_id, trans_type)))

            elif trans_type == 'BILL':
                validity = self.request.registry.settings[
                    'bimt.jvzoo_regular_period']
                user.valid_to = date.today() + timedelta(days=validity)
                user.enable()
                self.request.registry.notify(
                    UserEnabled(self.request, user, comment.format(
                        u'Enabled', trans_id, trans_type)))

            elif trans_type in ['RFND', 'CGBK', 'INSF']:
                user.valid_to = date.today()
                user.disable()
                self.request.registry.notify(
                    UserDisabled(self.request, user, comment.format(
                        u'Disabled', trans_id, trans_type)))

            else:
                raise ValueError(
                    u'Unknown Transaction Type "{}".'.format(trans_type))

            return 'Done.'

        except Exception as ex:
            msg = 'POST handling failed: {}: {}'.format(
                ex.__class__.__name__, ex.message)
            logger.warning(msg)
            return msg

    def _verify_POST(self):
        """Verifies if received POST is a valid JVZoo POST request.

        :return: True if verified, raise ValueError if verification failed.
        :rtype: bool
        """
        self.request.POST['secretkey'] = self.request.registry.settings[
            'bimt.jvzoo_secret_key']

        # concatenate POST parameters into a string
        strparams = u''
        for key, value in sorted(self.request.POST.items()):
            if key not in ['cverify', 'secretkey']:
                strparams += unicode(value + '|', 'utf-8')

        # secretkey must be last
        strparams += self.request.POST['secretkey']

        # calculate SHA digest and compare to ``cverify`` value
        sha = hashlib.sha1(strparams.encode('utf-8')).hexdigest().upper()
        if self.request.POST['cverify'] == sha[:8]:
            return True
        else:
            raise ValueError('Checksum verification failed.')

    def send_welcome_email(self, user, password):
        """Send a welcome email to the user, containing login credentials."""
        app_title = self.request.registry.settings['bimt.app_title']
        mailer = get_mailer(self.request)
        mailer.send(Message(
            subject=u'Welcome to {}!'.format(app_title),
            recipients=[user.email, ],
            body=render(
                'pyramid_bimt:templates/email_welcome.pt',
                {
                    'fullname': user.fullname,
                    'username': user.email,
                    'password': password,
                    'login_url': self.request.route_url('login'),
                    'app_title': app_title,
                    'year': date.today().year,
                },
            ),
        ))
