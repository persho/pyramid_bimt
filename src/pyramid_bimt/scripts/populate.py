# -*- coding: utf-8 -*-
"""Populate the DB with default content."""

from pyramid.paster import bootstrap
from pyramid_basemodel import Session
from pyramid_bimt import events
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import MailingTriggers
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import PortletPositions
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty

import argparse
import sys
import inspect
import re
import transaction

# This is a result of calling encrypt('secret'), and we have it pre-computed
# here so we don't have to compute it on every test setUp
SECRET_ENC = u'$6$rounds=90000$hig2KnPEdjRThLyK$UzWLANWcJzO6YqphWT5nbSC4'\
    'RkYKLIvSbAT/XnsO4m6xtr5qsw5d4glhJWzonIqpBocwXiS9qMpia46woVSBc0'


def default_audit_log_event_types():
    """Return a list of all default Audit log event types.

    This is normally used in scripts that populate DB with initial data.

    :return: All default Audit log event types.
    :rtype: list of AuditLogEventType objects
    """
    types = []
    for name, obj in inspect.getmembers(events, inspect.isclass):
        if (
            issubclass(obj, events.PyramidBIMTEvent)
            and name != 'PyramidBIMTEvent'
        ):
            types.append(AuditLogEventType(
                name=name,
                title=u' '.join(re.findall('[A-Z][^A-Z]*', name)),
                description=unicode(obj.__doc__),
            ))
    return types


def add_audit_log_event_types():
    """Init the Audit Log event types."""
    with transaction.manager:
        types = default_audit_log_event_types()
        for type_ in types:
            Session.add(type_)


def add_groups():
    """Init the 'admins', 'enabled', 'trial', 'unsubscribed' groups."""
    with transaction.manager:
        admins = Group(name='admins')
        Session.add(admins)

        enabled = Group(name='enabled')
        Session.add(enabled)

        trial = Group(name='trial')
        Session.add(trial)

        unsubscribed = Group(name='unsubscribed')
        Session.add(unsubscribed)


def add_users():
    """Init the 'admin@bar.com' and 'one@bar.com' user accounts."""
    with transaction.manager:
        admins = Group.by_name('admins')
        enabled = Group.by_name('enabled')
        trial = Group.by_name('trial')

        admin = User(
            email=u'admin@bar.com',
            password=SECRET_ENC,
            fullname=u'Ädmin',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        admin.groups.append(admins)
        admin.groups.append(enabled)
        Session.add(admin)

        # Init the normal user account
        one = User(
            email=u'one@bar.com',
            password=SECRET_ENC,
            fullname=u'Öne Bar',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        one.groups.append(enabled)
        one.groups.append(trial)
        Session.add(one)


def add_portlets():
    """Create a dummy portlet."""
    with transaction.manager:
        admins = Group.by_name('admins')

        portlet = Portlet(
            name='dummy',
            groups=[admins, ],
            position=PortletPositions.below_sidebar.name,
            weight=-127,
            html=u'You are admin.',
        )
        Session.add(portlet)


def add_mailings():
    """Create a dummy mailing."""
    with transaction.manager:
        trial = Group.by_name('trial')
        admins = Group.by_name('admins')

        mailing = Mailing(
            name='welcome_email',
            groups=[trial, ],
            exclude_groups=[admins, ],
            trigger=MailingTriggers.after_created.name,
            days=1,
            subject=u'Über Welcome!',
            body=u'Welcome to this über amazing BIMT app!',
        )
        Session.add(mailing)


def add_default_content():  # pragma: no cover (bw compat only)

    add_audit_log_event_types()
    add_groups()
    add_users()


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.expire_subscriptions etc/production.ini',
    )
    parser.add_argument(
        'config', type=str, metavar='<config>',
        help='Pyramid application configuration file.')

    env = bootstrap(parser.parse_args().config)
    add_default_content()

    env['closer']()
    print 'DB populated with dummy data.'  # noqa


if __name__ == '__main__':
    main()
