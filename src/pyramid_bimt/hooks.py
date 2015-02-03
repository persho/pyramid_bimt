# -*- coding: utf-8 -*-
"""Various helpers."""
from pyramid.events import BeforeRender
from pyramid.events import subscriber
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.models import User


def get_authenticated_user(request):
    """Get the authenticated user for this ``request``, if there is one."""
    email = request.unauthenticated_userid
    if email:
        return User.by_email(email)


@subscriber(BeforeRender)
def add_global(event):
    event['BimtPermissions'] = BimtPermissions
