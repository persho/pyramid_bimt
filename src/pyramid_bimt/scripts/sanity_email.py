# -*- coding: utf-8 -*-
"""Send sanity email."""

from datetime import date
from pyramid.renderers import render
from pyramid_basemodel import Session
from pyramid_bimt.views.misc import get_user_errors
from pyramid_mailer import mailer_factory_from_settings
from pyramid_mailer.message import Message
from pyramid.paster import bootstrap
from sqlalchemy import engine_from_config

import logging
import os
import sys

logger = logging.getLogger(__name__)


def send_sanity_mail(settings):

    mailer = mailer_factory_from_settings(settings)
    mail_address = settings['mail.default_sender']
    errors = get_user_errors()

    body = render(
        'pyramid_bimt:templates/bimt_sanity_mail.pt',
        {'errors': errors}
    )
    if errors:
        subject = 'Bimt sanity check errors on day: {}'.format(date.today())
    else:
        subject = 'Bimt sanity check is OK!'
    message = Message(
        subject=subject,
        sender=mail_address,
        recipients=[mail_address, ],
        body=body,
    )
    mailer.send(message)


def main(argv=sys.argv):
    env = bootstrap('etc/production.ini')
    settings = env['registry'].settings

    if 'sqlalchemy.url' in settings:
        db_url = settings['sqlalchemy.url']
    else:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise KeyError('DATABASE_URL not set, please set it.')

    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    send_sanity_mail(settings)

    env['closer']()
    logger.info('Sanity check email sent succesfully.')


if __name__ == '__main__':
    main()
