# -*- coding: utf-8 -*-
"""TODO:"""

from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid_bimt.models import User

import logging

logger = logging.getLogger(__name__)


def groupfinder(userid, request):
    user = User.get(userid)
    if user and user.groups:
        return ['g:%s' % g.name for g in user.groups]
    else:
        return []


class UserFactory(object):
    __acl__ = [
        (Allow, u'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        user = User.get(key)
        if user:
            user.__parent__ = self
            user.__name__ = key
            return user
        else:
            raise KeyError
