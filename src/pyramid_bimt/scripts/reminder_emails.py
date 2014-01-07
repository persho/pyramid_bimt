# -*- coding: utf-8 -*-
"""Send reminder emails to users."""

from datetime import date
from dateutil.relativedelta import relativedelta
from pyramid.paster import get_appsettings
from pyramid.renderers import render
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from pyramid_mailer import mailer_factory_from_settings
from pyramid_mailer.message import Message
from sqlalchemy import engine_from_config

import argparse
import json
import logging
import os
import sys


logger = logging.getLogger(__name__)

EMAIL_TEMPLATES = [
    {
        'name': 'first', 'template': 'first_email_reminder.pt',
        'subject': u'First payment reminder for {} membership'
    }, {
        'name': 'second', 'template': 'second_email_reminder.pt',
        'subject': u'Second payment reminder for {} membership'
    }, {
        'name': 'third', 'template': 'third_email_reminder.pt',
        'subject': u'Last reminder before your {} membership is cancelled'
    }, {
        'name': 'fourth', 'template': 'fourth_email_reminder.pt',
        'subject': u'Your {} membership has been cancelled'
    },
]


def get_reminder_template(user, today, named_deltas):
    for name, delta in named_deltas.items():
        if today - delta == user.valid_to:
            for template in EMAIL_TEMPLATES:
                if template['name'] == name:
                    return template
    return None


def send_reminder_email(
        mailer, user, template, app_title, pricing_page_url, default_sender
):
    body = render(
        'pyramid_bimt:templates/' + template['template'],
        {
            'fullname': user.fullname,
            'app_title': app_title,
            'pricing_page_url': pricing_page_url
        }
    )
    message = Message(
        subject=template['subject'].format(app_title),
        sender=default_sender,
        recipients=[user.email, ],
        body=body,
    )
    mailer.send(message)


def reminder_emails(date, settings, dry_run=True):
    deltas_json = settings['bimt.payment_reminders']
    if not dry_run:  # pragma: no cover
        mailer = mailer_factory_from_settings(settings)

    named_deltas = {}
    for k, v in json.loads(deltas_json).items():
        named_deltas.update({k: relativedelta(**v)})

    for user in User.get_enabled():
        template = get_reminder_template(user, date, named_deltas)
        if template:
            if not dry_run:  # pragma: no cover
                send_reminder_email(
                    mailer, user.email, template,
                    settings['bimt.app_title'],
                    settings['mail.default_sender'],
                    settings['bimt.pricing_page_url'],
                )
            logger.info(u'Sent reminder email with template name {} to '
                        'user {}, who is valid to {}.'.format(
                            template['name'], user.email, user.valid_to
                        ))


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Reminder emails script.',
                                     add_help=False)
    parser.add_argument('config', type=str, metavar='<config>',
                        help='Pyramid application configuration file.')

    appsettings = get_appsettings(parser.parse_args().config)

    if 'sqlalchemy.url' in appsettings:
        db_url = appsettings['sqlalchemy.url']
    else:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise KeyError('DATABASE_URL not set, please set it.')

    engine = engine_from_config(appsettings, 'sqlalchemy.')
    Session.configure(bind=engine)

    reminder_emails(date.today(), appsettings, dry_run=False)

    logger.info('Reminder emails script finished.')


if __name__ == '__main__':
    main()
