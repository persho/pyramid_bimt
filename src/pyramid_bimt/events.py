# -*- coding: utf-8 -*-
"""Provides events triggered on user creation, login, logout, etc."""

from pyramid_basemodel import Session
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implementer


class IUserCreated(Interface):
    """An event type that is emitted after a new user is created."""

    request = Attribute('The request object.')
    user = Attribute('The user who was created.')


class IUserLoggedIn(Interface):
    """An event type that is emitted after a user logs in."""

    request = Attribute('The request object.')
    user = Attribute('The user who logged in.')


class IUserLoggedOut(Interface):
    """An event type that is emitted after a user logs out."""

    request = Attribute('The request object')
    user = Attribute('The user who logged out.')


class IUserChangedPassword(Interface):
    """An event type that is emitted after a user changes its password."""

    request = Attribute('The request object')
    user = Attribute('The user who changes its password.')


class IUserDeleted(Interface):
    """An event type that is emitted whenever a user confirms an email
    address, typically by clicking on a link received by email."""

    request = Attribute('The request object')
    user = Attribute('The user who owns the email address.')


class PyramidBIMTEvent(object):
    """A base class for events raised by pyramid_bimt package."""

    def log_event(self):
        from pyramid_bimt.models import AuditLogEntry
        from pyramid_bimt.models import AuditLogEventType
        event_type = AuditLogEventType.get(name=self.__class__.__name__)
        entry = AuditLogEntry(
            user_id=self.user.id,
            event_type_id=event_type.id,
        )
        Session.add(entry)


@implementer(IUserCreated)
class UserSignedUp(PyramidBIMTEvent):
    """Emitted whenever a new user is created."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data
        self.log_event()


@implementer(IUserLoggedIn)
class UserLoggedIn(PyramidBIMTEvent):
    """Emitted whenever a user logs in."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data
        self.log_event()


@implementer(IUserLoggedOut)
class UserLoggedOut(PyramidBIMTEvent):
    """Emitted whenever a user logs out."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data
        self.log_event()


@implementer(IUserChangedPassword)
class UserChangedPassword(PyramidBIMTEvent):
    """Emitted whenever a user changes its password."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data
        self.log_event()


@implementer(IUserDeleted)
class UserDeleted(PyramidBIMTEvent):
    """Emitted whenever a user is deleted."""

    def __init__(self, request, username, data=None):
        self.request = request
        self.username = username
