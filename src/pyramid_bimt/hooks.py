# -*- coding: utf-8 -*-
"""Various helpers."""
from pyramid_bimt.models import User


def get_authenticated_user(request):
    """Get the authenticated user for this ``request``, if there is one."""
    email = request.unauthenticated_userid
    if email:
        return User.by_email(email)
