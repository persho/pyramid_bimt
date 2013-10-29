# -*- coding: utf-8 -*-
"""Provides events triggered on user creation, login, logout, etc."""

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


@implementer(IUserCreated)
class UserSignedUp(object):
    """An instance of this class is emitted whenever a new user is created."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data


@implementer(IUserLoggedIn)
class UserLoggedIn(object):
    """An instance of this class is emitted whenever a user logs in."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data


@implementer(IUserLoggedOut)
class UserLoggedOut(object):
    """An instance of this class is emitted whenever a user logs out."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data


@implementer(IUserChangedPassword)
class UserChangedPassword(object):
    """An instance of this class is emitted whenever a password is changed."""

    def __init__(self, request, user, data=None):
        self.request = request
        self.user = user
        self.data = data


@implementer(IUserDeleted)
class UserDeleted(object):
    """An instance of this class is emitted whenever a user is deleted."""

    def __init__(self, request, username, data=None):
        self.request = request
        self.username = username
