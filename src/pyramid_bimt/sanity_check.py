# -*- coding: utf-8 -*-
"""Regular checks if our data is sane."""

from pyramid.view import view_config
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets


@view_config(
    route_name='sanity_check',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/sanity_check.pt',
)
def sanity_check_view(request):
    """An admin view for manual sanity checks."""
    app_assets.need()
    warnings = sanity_check()
    return {
        'warnings': warnings,
    }


def sanity_check():
    """Find sanity check warnings.

    :returns: sanity check warnings
    :rtype: list of strings
    """
    warnings = []

    warnings = warnings + check_admin_user()
    warnings = warnings + check_default_groups()

    for user in User.get_all():
        warnings = warnings + check_user(user)
    return warnings


def check_admin_user():
    warnings = []
    user = User.by_id(1)

    if not user:
        warnings.append('User "admin" should have id of "1".')
    if user and not user.enabled:
        warnings.append('User "admin" should be enabled.')
    if user and Group.by_name('admins') not in user.groups:
        warnings.append('User "admin" should be in "admins" group.')
    return warnings


def check_default_groups():
    warnings = []
    if not Group.by_name('admins'):
        warnings.append('Group "admins" missing.')
    if not Group.by_name('enabled'):
        warnings.append('Group "enabled" missing.')
    if not Group.by_name('trial'):
        warnings.append('Group "trial" missing.')
    return warnings


def check_user(user):
    """Get warnings related to user's membership in different groups.

    :param user: user to be checked
    :type user: :class:`pyramid_bimt.models.User`
    :returns: warnings for given user
    :rtype: list of strings
    """
    warnings = []
    if not user.fullname:
        warnings.append(
            'User {} ({}) has an empty fullname.'.format(user.email, user.id))

    return warnings
