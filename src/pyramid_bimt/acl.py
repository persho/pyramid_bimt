# -*- coding: utf-8 -*-
"""TODO:"""

from pyramid.httpexceptions import HTTPFound
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import User

import logging

logger = logging.getLogger(__name__)


def groupfinder(userid, request):
    user = User.get(userid)
    if user and user.groups:
        return ['g:{}'.format(g.name) for g in user.groups]
    else:
        return []


class RootFactory(object):
    __acl__ = [
        (Allow, Authenticated, 'personal'),
        (Allow, 'g:users', 'user'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request


class UserFactory(object):
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        if request.get('PATH_INFO') == '/users/':
            raise HTTPFound(location=request.route_path('users'))
        self.request = request

    def __getitem__(self, key):
        try:
            user_id = int(key)
            user = User.get_by_id(user_id)
            if user:
                user.__parent__ = self
                user.__name__ = key
                return user
            else:
                raise KeyError
        except ValueError:
            raise KeyError


class AuditLogFactory(object):
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        entry = AuditLogEntry.get(key)
        if entry:
            entry.__parent__ = self
            entry.__name__ = key
            return entry
        else:
            raise KeyError
