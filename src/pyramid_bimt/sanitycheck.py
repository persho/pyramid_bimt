# -*- coding: utf-8 -*-
"""Regular checks if our data is sane."""

from pyramid.view import view_config
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.events import SanityCheckDone
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound
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
    permission=BimtPermissions.manage,
    layout='default',
    renderer='pyramid_bimt:templates/sanitycheck.pt',
)
def sanitycheck_view(request):
    """An admin view for manual sanity checks."""
    app_assets.need()
    warnings = run_all_checks(request)
    return {
        'warnings': warnings,
    }


def run_all_checks(request):
    """Find all sanity checks and run them.

    :returns: sanitycheck warnings
    :rtype: list of strings
    """
    warnings = []
    for check in request.registry.getAllUtilitiesRegisteredFor(ISanityCheck):
        warnings += check()()
    if warnings:
        comment = u', '.join(warnings)
    else:
        comment = u'Sanity check finished without any warnings.'

    request.registry.notify(
        SanityCheckDone(request, User.by_id(1), comment=comment)
    )

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


class CheckUsersProductGroup:
    implements(ISanityCheck)

    def __call__(self):
        warnings = []
        for user in User.get_all():
            try:
                user.product_group
            except NoResultFound:
                pass  # continue to next user
            except MultipleResultsFound:
                warnings.append(
                    'User {} ({}) has multiple product groups.'.format(
                        user.email, user.id))

        return warnings


class CheckUsersEnabledDisabled:
    implements(ISanityCheck)

    def __call__(self):
        warnings = []
        enabled_event_id = AuditLogEventType.by_name('UserEnabled').id
        disabled_event_id = AuditLogEventType.by_name('UserDisabled').id
        for user in User.get_all():
            last_enabled_entry = AuditLogEntry.get_all(
                security=False,
                filter_by={
                    'event_type_id': enabled_event_id,
                    'user_id': user.id
                },
                order_by='timestamp'
            ).first()
            last_disabled_entry = AuditLogEntry.get_all(
                security=False,
                filter_by={
                    'event_type_id': disabled_event_id,
                    'user_id': user.id
                },
                order_by='timestamp'
            ).first()

            if user.enabled:
                if not last_enabled_entry:
                    warnings.append(
                        'User {} ({}) is enabled, '
                        'but has no UserEnabled entry.'.format(
                            user.email, user.id))

                elif last_disabled_entry and (
                        last_enabled_entry.timestamp < last_disabled_entry.timestamp):  # noqa
                    warnings.append(
                        'User {} ({}) is enabled, '
                        'but has an UserDisabled entry '
                        'after UserEnabled entry.'.format(
                            user.email, user.id))

            else:
                if not last_disabled_entry:
                    warnings.append(
                        'User {} ({}) is disabled, '
                        'but has no UserDisabled entry.'.format(
                            user.email, user.id))

                elif last_enabled_entry and (
                        last_disabled_entry.timestamp < last_enabled_entry.timestamp):  # noqa
                    warnings.append(
                        'User {} ({}) is disabled, '
                        'but has an UserEnabled entry '
                        'after UserDisabled entry.'.format(
                            user.email, user.id))

        return warnings
