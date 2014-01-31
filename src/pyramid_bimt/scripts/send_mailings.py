# -*- coding: utf-8 -*-
"""Find mailings that should be sent today and send them."""

from datetime import date
from datetime import timedelta
from pyramid.paster import bootstrap
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import User
from pyramid_bimt.models import MailingTriggers
from sqlalchemy.sql.expression import func

import argparse
import logging
import sys
import transaction

logger = logging.getLogger(__name__)


def send_mailings():
    with transaction.manager:  # so send() will actually send emails
        for mailing in Mailing.query.all():
            if mailing.trigger == MailingTriggers.after_created.name:
                for user in User.query.filter(
                    func.date(User.created) == func.date(
                        date.today() - timedelta(days=mailing.days))
                ).all():
                    mailing.send(user)
                    logger.info('Sent mailing "{}" for user "{}" ({}).'.format(
                        mailing.name, user.email, user.id))

            elif mailing.trigger == MailingTriggers.after_last_payment.name:
                for user in User.query.filter(
                    func.date(User.last_payment) == func.date(
                        date.today() - timedelta(days=mailing.days))
                ).all():
                    mailing.send(user)
                    logger.info('Sent mailing "{}" for user "{}" ({}).'.format(
                        mailing.name, user.email, user.id))

            elif mailing.trigger == MailingTriggers.before_valid_to.name:
                for user in User.query.filter(
                    func.date(User.valid_to) == func.date(
                        date.today() + timedelta(days=mailing.days))
                ).all():
                    mailing.send(user)
                    logger.info('Sent mailing "{}" for user "{}" ({}).'.format(
                        mailing.name, user.email, user.id))


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.send_mailings etc/production.ini',
    )
    parser.add_argument(
        'config', type=str, metavar='<config>',
        help='Pyramid application configuration file.')

    env = bootstrap(parser.parse_args().config)
    send_mailings()

    env['closer']()
    logger.info('Send mailings script finished.')


if __name__ == '__main__':
    main()
