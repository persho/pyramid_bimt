# -*- coding: utf-8 -*-
"""Miscellaneous helpers and tools views."""

from datetime import datetime
from pyramid.httpexceptions import exception_response
from pyramid.view import view_config
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets

import os


@view_config(
    route_name='raise_http_error',
    permission='admin',
)
def raise_http_error(request):
    raise exception_response(int(request.matchdict['error_code']))


@view_config(
    route_name='raise_js_error',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/form.pt',
)
def raise_js_error(request):
    app_assets.need()
    return {
        'title': 'JS error',
        'form': """<script type="text/javascript">
      throw new Error('[{now}] Error test.');
    </script>

    <p>[{now}] Error test.</p>""".format(now=datetime.utcnow())
    }


@view_config(
    route_name='config',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/config.pt',
)
def config(request):
    app_assets.need()
    request.layout_manager.layout.hide_sidebar = True
    settings = sorted(request.registry.settings.items(), key=lambda x: x[0])
    environ = sorted(os.environ.items(), key=lambda x: x[0])
    return {
        'title': 'Config',
        'environ': environ,
        'settings': settings
    }


@view_config(
    route_name='sanity_check',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/sanity_view.pt',
)
def bimt_sanity_check(request):
    app_assets.need()
    errors = get_user_errors()
    return {
        'errors': errors
    }


def get_user_errors():
    """
    Errors for all users in our application

    :returns: errors for all users
    :rtype:   list
    """
    errors = []
    for user in User.get_all():
        errors = errors + check_user(user)
    return errors


def check_user(user):
    """
    Get errors related to user's membership in different groups.

    :param    user: user to be checked
    :type     user: User

    :returns: Errors for that user
    :rtype:   list
    """
    errors = []
    if not user.enabled:
        if user.trial:
            errors.append(
                'User {0} is disabled but in trial group!'.format(user.id)
            )
        if user.regular:
            errors.append(
                'User {0} is disabled but in regular group!'.format(user.id)
            )
    if user.enabled and not (user.trial or user.regular):
        errors.append(
            'User {0} is enabled but not trial or regular!'.format(user.id)
        )
    if user.trial and user.regular:
        errors.append(
            'User {0} is both trial and regular!'.format(user.id)
        )
    return errors
