# -*- coding: utf-8 -*-
"""Populate the DB with default content."""

from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid_bimt import events
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from sqlalchemy import engine_from_config

import inspect
import os
import re
import sys
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
        Session.flush()


def add_groups():
    """Init the 'admins', 'enabled', 'trial', 'regular' groups."""
    with transaction.manager:
        admins = Group(name='admins')
        Session.add(admins)
        Session.flush()

        enabled = Group(name='enabled')
        Session.add(enabled)
        Session.flush()

        trial = Group(name='trial')
        Session.add(trial)
        Session.flush()

        regular = Group(name='regular')
        Session.add(regular)
        Session.flush()


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


def add_default_content():  # pragma: no cover (bw compat only)

    add_audit_log_event_types()
    add_groups()
    add_users()


def main(argv=sys.argv):

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print 'DATABASE_URL not set, using default SQLite db.'  # noqa
        db_url = 'sqlite:///./bimt-app.db'

    settings = {'sqlalchemy.url': db_url}
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

    add_default_content()
    print 'DB populated with dummy data: {0}'.format(db_url)  # noqa


if __name__ == '__main__':
    main()
