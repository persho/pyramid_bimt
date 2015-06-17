# -*- coding: utf-8 -*-
"""Find users with expired `valid_to` and disable them."""

from datetime import date
from datetime import datetime
from pyramid.paster import bootstrap
from pyramid.paster import setup_logging
from pyramid_basemodel import Session
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
from pyramid_bimt.models import User

import argparse
import logging
import sys
import transaction

logger = logging.getLogger(__name__)


def expire_subscriptions():
    """Find all outstanding subscriptions and expire them."""
    with transaction.manager:
        for user in User.get_all():
            if user.enabled:
                if user.valid_to < date.today():
                    user.disable()
                    msg = u'Disabled user {} ({}) because its valid_to ({}) ' \
                        'has expired.'.format(
                            user.email, user.id, user.valid_to)
                    Session.add(AuditLogEntry(
                        user_id=user.id,
                        event_type_id=AuditLogEventType.by_name(
                            'UserDisabled').id,
                        comment=msg,
                    ))
                    logger.info(msg)
                    continue

                # handle addons
                for prop in user.properties:
                    if not prop.key.startswith('addon_'):
                        continue
                    if not prop.key.endswith('_valid_to'):
                        continue
                    valid_to = datetime.strptime(prop.value, '%Y-%m-%d').date()
                    if valid_to >= date.today():
                        continue
                    group = Group.by_product_id(
                        prop.key.split('addon_')[1].split('_valid_to')[0])
                    user.groups.remove(group)
                    msg = u'Addon "{}" disabled for user {} ({}) because ' \
                        'its valid_to ({}) has expired.'.format(
                            group.name, user.email, user.id, prop.value)
                    Session.add(AuditLogEntry(
                        user_id=user.id,
                        event_type_id=AuditLogEventType.by_name(
                            'UserDisabled').id,
                        comment=msg,
                    ))


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.expire_subscriptions etc/production.ini',
    )
    parser.add_argument(
        'config', type=str, metavar='<config>',
        help='Pyramid application configuration file.')

    env = bootstrap(parser.parse_args().config)
    setup_logging(parser.parse_args().config)

    expire_subscriptions()

    env['closer']()
    logger.info('Expire subscription script finished.')


if __name__ == '__main__':
    main()
