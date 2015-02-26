# -*- coding: utf-8 -*-
"""Populate the DB with default content."""

from pyramid.paster import bootstrap
from pyramid_basemodel import Session
from pyramid_bimt import events
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
from pyramid_bimt.models import GroupProperty
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import MailingTriggers
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import PortletPositions
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty

import argparse
import inspect
import re
import sys
import transaction

# This is a result of calling encrypt('secret'), and we have it pre-computed
# here so we don't have to compute it on every test setUp
SECRET_ENC = u'$6$rounds=90000$hig2KnPEdjRThLyK$UzWLANWcJzO6YqphWT5nbSC4'\
    'RkYKLIvSbAT/XnsO4m6xtr5qsw5d4glhJWzonIqpBocwXiS9qMpia46woVSBc0'

PASSWORD_EMAIL_BODY = u"""
<p>Your new password for ${settings['bimt.app_title']} is: ${password}</p>
<p>Login to the members' area: ${request.route_url('login')}</p>
"""

USER_CREATED_BODY = u"""
<p>
  here are your login details for the membership area:<br>
  u: ${user.email}<br>
  p: ${password}
</p>
<p tal:condition="python: user.get_property('api_key', None)">
  Here is your API key for integrating with other services: <br />
  API key: ${python: user.get_property('api_key')}
</p>
<p>Login to the members' area: ${request.route_url('login')}</p>
"""


def default_audit_log_event_types():
    """Return a list of all default Audit log event types.

    This is normally used in scripts that populate DB with initial data.

    :return: All default Audit log event types.
    :rtype: list of AuditLogEventType objects
    """
    types = []
    for name, obj in inspect.getmembers(events, inspect.isclass):
        if (
            issubclass(obj, events.PyramidBIMTEvent) and
            name != 'PyramidBIMTEvent'
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
        admins = Group(
            name='admins',
            properties=[GroupProperty(key=u'bimt', value=u'on'), ],
        )
        Session.add(admins)

        staff = Group(
            name='staff',
            properties=[GroupProperty(key=u'bimt', value=u'on'), ],
        )
        Session.add(staff)

        enabled = Group(
            name='enabled',
            properties=[GroupProperty(key=u'bimt', value=u'on'), ],
        )
        Session.add(enabled)

        trial = Group(
            name='trial',
            properties=[GroupProperty(key=u'bimt', value=u'on'), ],
        )
        Session.add(trial)

        unsubscribed = Group(
            name='unsubscribed',
            properties=[GroupProperty(key=u'bimt', value=u'on'), ],
        )
        Session.add(unsubscribed)

        impersonators = Group(
            name='impersonators',
            properties=[GroupProperty(
                key=u'description',
                value=u'Members can impersonate other users with login-as'), ],
        )
        Session.add(impersonators)


def add_users():
    """Init the 'admin@bar.com' and 'one@bar.com' user accounts."""
    with transaction.manager:
        admins = Group.by_name('admins')
        staff = Group.by_name('staff')
        enabled = Group.by_name('enabled')
        trial = Group.by_name('trial')

        # Create the admin user account
        admin = User(
            email=u'admin@bar.com',
            password=SECRET_ENC,
            fullname=u'Ädmin',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        admin.groups.append(admins)
        admin.groups.append(enabled)
        Session.add(admin)

        # Create the staff member account
        staff_member = User(
            email=u'staff@bar.com',
            password=SECRET_ENC,
            fullname=u'Stäff Member',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        staff_member.groups.append(enabled)
        staff_member.groups.append(staff)
        Session.add(staff_member)

        # Create the normal user account
        one = User(
            email=u'one@bar.com',
            billing_email=u'billing@bar.com',
            password=SECRET_ENC,
            fullname=u'Öne Bar',
            properties=[UserProperty(key=u'bimt', value=u'on'), ],
        )
        one.groups.append(enabled)
        one.groups.append(trial)
        Session.add(one)


def add_mailings(app_title=u'BIMT'):
    """Create default mailings."""
    with transaction.manager:

        mailing_created = Mailing(
            name='after_creation',
            trigger=MailingTriggers.after_user_created.name,
            days=0,
            subject=u'Welcome to {settings[bimt.app_title]}!',
            body=USER_CREATED_BODY,
        )
        Session.add(mailing_created)

        mailing_disabled = Mailing(
            name='after_disabled',
            trigger=MailingTriggers.after_user_disabled.name,
            days=0,
            subject=u'Your {} account is disabled.'.format(app_title),
            body=u'Your account is disabled.',
        )
        Session.add(mailing_disabled)

        mailing_password_changed = Mailing(
            name='after_user_changed_password',
            trigger=MailingTriggers.after_user_changed_password.name,
            days=0,
            subject=u'{} Password Reset'.format(app_title),
            body=PASSWORD_EMAIL_BODY,
        )
        Session.add(mailing_password_changed)


def add_demo_mailing():
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


def add_demo_portlet():
    """Create a dummy portlet."""
    with transaction.manager:
        admins = Group.by_name('admins')
        enabled = Group.by_name('enabled')

        portlet = Portlet(
            name='dummy',
            groups=[admins, ],
            exclude_groups=[enabled, ],
            position=PortletPositions.below_sidebar.name,
            weight=-127,
            html=u'You are admin.',
        )
        Session.add(portlet)


def add_demo_auditlog_entries():
    """Add a dummy audit-log entry."""
    with transaction.manager:
        read = AuditLogEntry(
            user=User.by_email('staff@bar.com'),
            event_type_id=2,
            comment='read entry',
            read=True,
        )
        Session.add(read)

        unread = AuditLogEntry(
            user=User.by_email('one@bar.com'),
            event_type_id=2,
            comment='unread entry',
            read=False,
        )
        Session.add(unread)


def add_default_content():  # pragma: no cover (bw compat only)

    add_audit_log_event_types()
    add_groups()
    add_users()
    add_mailings()


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        usage='bin/py -m '
        'pyramid_bimt.scripts.populate etc/production.ini',
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
