# -*- coding: utf-8 -*-
"""Send sanity check report to email."""

from pyramid.paster import bootstrap
from pyramid.paster import setup_logging
from pyramid.renderers import render
from pyramid_bimt.sanitycheck import run_all_checks
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

import argparse
import logging
import sys

logger = logging.getLogger(__name__)


def send_email(settings, request, verbose=False):
    warnings = run_all_checks(request)
    if warnings:
        subject = '{} sanity check found {} warnings'.format(
            settings['bimt.app_title'], len(warnings))
    else:
        subject = '{} sanity check OK'.format(settings['bimt.app_title'])
    if warnings or verbose:
        mailer = get_mailer(request)
        mailer.send_immediately(Message(
            recipients=[settings['mail.default_sender'], ],
            subject=subject,
            html=render(
                'pyramid_bimt:templates/sanitycheck_email.pt',
                {'warnings': warnings},
            ),
        ))


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.sanitycheck_email etc/production.ini',
    )
    parser.add_argument(
        'config', type=str, metavar='<config>',
        help='Pyramid application configuration file.')
    parser.add_argument(
        '-v', '--verbose',
        help='Send email regardless of sanity check result.',
        action='store_true',
    )

    env = bootstrap(parser.parse_args().config)
    setup_logging(parser.parse_args().config)
    verbose = parser.parse_args().verbose

    settings = env['registry'].settings
    request = env['request']
    send_email(settings, request, verbose=verbose)

    env['closer']()
    logger.info('Sanity check email sent successfully.')


if __name__ == '__main__':
    main()
