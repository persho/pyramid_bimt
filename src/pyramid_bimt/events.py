# -*- coding: utf-8 -*-

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


class IUserEnabled(Interface):
    """An event type that is emitted whenever a user is enabled, meaning
    it is put in the 'users' group and can access app views."""

    request = Attribute('The request object')
    user = Attribute('The user who was enabled.')


class IUserDisabled(Interface):
    """An event type that is emitted whenever a user is disabled, meaning
    it is removed from the 'users' group and can no longer access app views."""

    request = Attribute('The request object')
    user = Attribute('The user who was disabled.')


class IUserLoggedInAs(Interface):
    """An event type that is emitted after a user logs in as another user."""

    request = Attribute('The request object.')
    user = Attribute('The user who logged in.')


class ISanityCheckDone(Interface):
    """An event type that is emitted after a sanity check is done."""

    request = Attribute('The request object.')
    user = Attribute('The user who made the check.')


class IUserSubscriptionChanged(Interface):
    """An event type that is emitted after a user subscription is changed."""

    request = Attribute('The request object.')
    user = Attribute('The user who changed the subscription.')


class IUserSubscriptionChangeFailed(Interface):
    """An event type that is emitted after a user subscription change
    failed.
    """

    request = Attribute('The request object.')
    user = Attribute('The user who changed the subscription.')


class IReferralEmailSent(Interface):
    """An event type that is emitted after a user sends a referral email.
    """

    request = Attribute('The request object.')
    user = Attribute('The user who sent the referral email.')


class PyramidBIMTEvent(object):
    """A base class for events raised by pyramid_bimt package."""

    def __init__(self, request, user, comment=None):
        self.request = request
        self.user = user
        self.comment = comment
        self.log_event(comment=comment)

    def log_event(self, comment=None, read=False):
        from pyramid_bimt.models import AuditLogEntry
        from pyramid_bimt.models import AuditLogEventType
        event_type = AuditLogEventType.by_name(name=self.__class__.__name__)
        entry = AuditLogEntry(
            user_id=self.user.id,
            event_type_id=event_type.id,
            comment=comment,
            read=read,
        )
        Session.add(entry)


@implementer(IUserCreated)
class UserCreated(PyramidBIMTEvent):
    """Emitted whenever a new user is created."""

    def __init__(self, request, user, password, comment=None):
        self.request = request
        self.user = user
        self.password = password
        self.comment = comment
        self.log_event(comment=comment)


@implementer(IUserChangedPassword)
class UserChangedPassword(PyramidBIMTEvent):
    """Emitted whenever a user changes its password."""

    def __init__(self, request, user, password, comment=None):
        self.request = request
        self.user = user
        self.password = password
        self.comment = comment
        self.log_event(comment=comment)


@implementer(IUserLoggedIn)
class UserLoggedIn(PyramidBIMTEvent):
    """Emitted whenever a user logs in."""

    def __init__(self, request, user, comment=None, read=True):
        self.request = request
        self.user = user
        self.comment = comment
        self.log_event(comment=comment, read=read)


@implementer(IUserLoggedOut)
class UserLoggedOut(PyramidBIMTEvent):
    """Emitted whenever a user logs out."""

    def __init__(self, request, user, comment=None, read=True):
        self.request = request
        self.user = user
        self.comment = comment
        self.log_event(comment=comment, read=read)


@implementer(IUserEnabled)
class UserEnabled(PyramidBIMTEvent):
    """Emitted whenever a user is enabled."""


@implementer(IUserDisabled)
class UserDisabled(PyramidBIMTEvent):
    """Emitted whenever a user is disabled."""


@implementer(IUserLoggedInAs)
class UserLoggedInAs(PyramidBIMTEvent):
    """Emitted whenever a user logs in as another user."""


@implementer(ISanityCheckDone)
class SanityCheckDone(PyramidBIMTEvent):
    """Emitted whenever a sanity check is done."""


@implementer(IUserSubscriptionChanged)
class UserSubscriptionChanged(PyramidBIMTEvent):
    """Emitted whenever a user subscription is changed."""


@implementer(IUserSubscriptionChangeFailed)
class UserSubscriptionChangeFailed(PyramidBIMTEvent):
    """Emitted whenever a user subscription change failed."""


@implementer(IReferralEmailSent)
class ReferralEmailSent(PyramidBIMTEvent):
    """Emitted whenever a user sends a referral email."""
