# -*- coding: utf-8 -*-
"""Populate the DB with default content."""

from pyramid.paster import bootstrap
from pyramid_basemodel import Session
from pyramid_bimt import events
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
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
    """Init the 'admins', 'enabled', 'trial' groups."""
    with transaction.manager:
        admins = Group(name='admins')
        Session.add(admins)

        enabled = Group(name='enabled')
        Session.add(enabled)

        trial = Group(name='trial')
        Session.add(trial)


def add_users():
    """Init the 'admin@bar.com' and 'one@bar.com' user accounts."""
    with transaction.manager:
        admins = Group.by_name('admins')
        enabled = Group.by_name('enabled')

        admin = User(
            email=u'admin@bar.com',
            password=SECRET_ENC,
            fullname=u'Admin',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        admin.groups.append(admins)
        admin.groups.append(enabled)
        Session.add(admin)

        # Init the normal user account
        one = User(
            email=u'one@bar.com',
            password=SECRET_ENC,
            fullname=u'One Bar',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        one.groups.append(enabled)
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
