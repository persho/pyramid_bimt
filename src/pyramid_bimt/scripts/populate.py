# -*- coding: utf-8 -*-
"""Populate the DB with default content."""

from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import User, UserSettings
from pyramid_bimt.security import encrypt
from pyramid_bimt import events
from pyramid_bimt.models import AuditLogEventType

import inspect
import re
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
            email='admin@bar.com',
            password=encrypt('secret'),
            settings=[UserSettings(key="bnh", value="on")]
        )
        admin.groups.append(admins)
        admin.groups.append(users)
        Session.add(admin)
