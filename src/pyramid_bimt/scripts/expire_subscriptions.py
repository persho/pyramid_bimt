# -*- coding: utf-8 -*-
"""Find users with expired `valid_to` and disable them."""

from datetime import date
from pyramid.paster import bootstrap
from pyramid_basemodel import Session
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import User

import argparse
import sys
import transaction


def expire_subscriptions():
    with transaction.manager:
        for user in User.get_all():
            if user.enabled:
                if user.valid_to < date.today():
                    user.disable()
                    msg = u'Disabled user {} because its valid_to ({}) has ' \
                        'expired.'.format(user.id, user.valid_to)
                    Session.add(AuditLogEntry(
                        user_id=user.id,
                        event_type_id=AuditLogEventType.by_name(
                            'UserDisabled').id,
                        comment=msg,
                    ))
                    print msg  # noqa


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.expire_subscriptions etc/production.ini',
    )
    parser.add_argument(
        'config', type=str, metavar='<config>',
        help='Pyramid application configuration file.')

    env = bootstrap(parser.parse_args().config)
    expire_subscriptions()

    env['closer']()
    print 'Expire subscription script finished.'  # noqa


if __name__ == '__main__':
    main()
