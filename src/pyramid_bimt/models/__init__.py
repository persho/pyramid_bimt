# -*- coding: utf-8 -*-

# Marker object for checking if key parameter was passed
sentinel = object()


class GetByIdMixin(object):
    """A mixin for adding by_id method to models."""

    @classmethod
    def by_id(class_, id, default=sentinel):
        """Get a Model object by id."""
        try:
            id = int(id)
            return class_.query.filter_by(id=id).first()
        except (ValueError, TypeError) as exc:
            if default == sentinel:
                raise exc
            else:
                return default


class GetByNameMixin(object):
    """A mixin for adding by_name method to models."""

    @classmethod
    def by_name(class_, name, default=sentinel):
        """Get a Model object by name."""
        try:
            str(name).decode('ascii')
            return class_.query.filter_by(name=name).first()
        except UnicodeDecodeError as exc:
            if default == sentinel:
                raise exc
            else:
                return default


from .auditlog import AuditLogEntry  # noqa
from .auditlog import AuditLogEventType  # noqa
from .group import Group  # noqa
from .group import GroupProperty  # noqa
from .group import user_group_table  # noqa
from .mailing import Mailing  # noqa
from .mailing import MailingTriggers  # noqa
from .mailing import exclude_mailing_group_table  # noqa
from .mailing import mailing_group_table  # noqa
from .portlet import Portlet  # noqa
from .portlet import PortletPositions  # noqa
from .portlet import portlet_group_table  # noqa
from .user import User  # noqa
from .user import UserProperty  # noqa
from pyramid_basemodel import Session  # noqa
