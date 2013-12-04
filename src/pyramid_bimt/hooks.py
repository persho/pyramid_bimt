# -*- coding: utf-8 -*-
"""Various helpers."""


from pyramid_bimt.models import User
from pyramid.security import unauthenticated_userid
import logging
logger = logging.getLogger(__name__)


def get_authenticated_user(request):
    """Get the authenticated user for this ``request``, if there is one."""
    email = unauthenticated_userid(request)
    if email:
        return User.by_email(email)
