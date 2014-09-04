# -*- coding: utf-8 -*-
"""Access Control Level groupfinder and factories."""

from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import Group
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import User

import logging

logger = logging.getLogger(__name__)


def groupfinder(user_email, request):
    user = User.by_email(user_email)
    if user and user.groups:
        return ['g:{}'.format(g.name) for g in user.groups]
    else:
        return []


class RootFactory(object):
    __acl__ = [
        (Allow, 'g:enabled', 'user'),
        (Allow, 'g:staff', 'staff'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request


class UserFactory(object):
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
        (Allow, 'g:staff', 'manage_users'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        user = User.by_id(key)
        if user:
            user.__parent__ = self
            user.__name__ = key
            return user
        else:
            raise KeyError


class GroupFactory(object):
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
        (Allow, 'g:staff', 'manage_groups'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        group = Group.by_id(key)
        if group:
            group.__parent__ = self
            group.__name__ = key
            return group
        else:
            raise KeyError


class AuditLogFactory(object):
    __acl__ = [
        (Allow, 'g:enabled', 'user'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        entry = AuditLogEntry.by_id(key)
        if entry:
            entry.__parent__ = self
            entry.__name__ = key
            return entry
        else:
            raise KeyError


class PortletFactory(object):
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        portlet = Portlet.by_id(key)
        if portlet:
            portlet.__parent__ = self
            portlet.__name__ = key
            return portlet
        else:
            raise KeyError


class MailingFactory(object):
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        mailing = Mailing.by_id(key)
        if mailing:
            mailing.__parent__ = self
            mailing.__name__ = key
            return mailing
        else:
            raise KeyError
