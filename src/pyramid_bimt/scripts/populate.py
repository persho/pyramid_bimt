# -*- coding: utf-8 -*-
"""Populate the DB with default content."""

from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid_bimt import events
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from pyramid_bimt.security import encrypt
from sqlalchemy import engine_from_config

import inspect
import os
import re
import sys
import transaction


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


def add_default_content():

    with transaction.manager:

        # Init the Audit Log event types
        types = default_audit_log_event_types()
        for type_ in types:
            Session.add(type_)
        Session.flush()

        # Init the admins group
        admins = Group(name='admins')
        Session.add(admins)
        Session.flush()

        # Init the users group
        users = Group(name='users')
        Session.add(users)
        Session.flush()

        # Init the admin user account
        admin = User(
            email=u'admin@bar.com',
            password=encrypt('secret'),
            properties=[UserProperty(key=u"bimt", value=u"rocks"), ],
        )
        admin.groups.append(admins)
        admin.groups.append(users)
        Session.add(admin)


def main(argv=sys.argv):

    # TODO: check for DB existance etc.? this fails if run more than once
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print "DATABASE_URL not set, using default SQLite db."  # noqa
        db_url = "sqlite:///./bimt-app.db"

    settings = {'sqlalchemy.url': db_url}
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

    add_default_content()
    print "DB populated with dummy data: {0}".format(db_url)  # noqa


if __name__ == '__main__':
    main()
