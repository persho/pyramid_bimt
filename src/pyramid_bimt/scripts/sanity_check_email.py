# -*- coding: utf-8 -*-
"""Send sanity check report to email."""

from pyramid.paster import bootstrap
from pyramid.renderers import render
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid_bimt.sanity_check import sanity_check

import argparse
import logging
import sys

logger = logging.getLogger(__name__)


def send_email(settings, request):
    warnings = sanity_check()
    if warnings:
        subject = '{} sanity check found {} warnings'.format(
            settings['bimt.app_title'], len(warnings))
    else:
        subject = '{} sanity check OK'.format(settings['bimt.app_title'])

    mailer = get_mailer(request)
    mailer.send_immediately(Message(
        recipients=['maintenance@niteoweb.com', ],
        subject=subject,
        html=render(
            'pyramid_bimt:templates/sanity_check_email.pt',
            {'warnings': warnings},
        ),
    ))


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.sanity_check_email etc/production.ini',
    )
    parser.add_argument(
        'config', type=str, metavar='<config>',
        help='Pyramid application configuration file.')

    env = bootstrap(parser.parse_args().config)
    settings = env['registry'].settings
    request = env['request']
    send_email(settings, request)

    env['closer']()
    logger.info('Sanity check email sent successfully.')


if __name__ == '__main__':
    main()