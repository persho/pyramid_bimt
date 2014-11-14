# -*- coding: utf-8 -*-
"""Regular checks if our data is sane."""

from pyramid.view import view_config
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets
from zope.interface import Interface
from zope.interface import implements


class ISanityCheck(Interface):
    """Definition class for all sanity checks."""

    def __call__(self):  # pragma: no cover
        """Perform the check and return warnings as lines of strings.

        :returns: warnings found in this check
        :rtype: list of strings
        """
        pass


@view_config(
    route_name='sanitycheck',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/sanitycheck.pt',
)
def sanitycheck_view(request):
    """An admin view for manual sanity checks."""
    app_assets.need()
    warnings = run_all_checks(request.registry)
    return {
        'warnings': warnings,
    }


def run_all_checks(registry):
    """Find all sanity checks and run them.

    :returns: sanitycheck warnings
    :rtype: list of strings
    """
    warnings = []
    for check in registry.getAllUtilitiesRegisteredFor(ISanityCheck):
        warnings += check()()

    return warnings


class CheckAdminUser:
    implements(ISanityCheck)

    def __call__(self):
        warnings = []
        user = User.by_id(1)

        if not user:
            warnings.append('User "admin" should have id of "1".')
        if user and user.enabled:
            warnings.append('User "admin" should be disabled in production.')
        if user and Group.by_name('admins') not in user.groups:
            warnings.append('User "admin" should be in "admins" group.')
        return warnings


class CheckDefaultGroups:
    implements(ISanityCheck)

    def __call__(self):
        warnings = []
        if not Group.by_name('admins'):
            warnings.append('Group "admins" missing.')
        if not Group.by_name('enabled'):
            warnings.append('Group "enabled" missing.')
        if not Group.by_name('trial'):
            warnings.append('Group "trial" missing.')
        return warnings


class CheckUsersProperties:
    implements(ISanityCheck)

    def __call__(self):
        warnings = []
        for user in User.get_all():
            if user.fullname is None or not user.fullname.strip():
                warnings.append(
                    'User {} ({}) has an empty fullname.'.format(
                        user.email, user.id))

        return warnings
