# -*- coding: utf-8 -*-
"""Models mixins and utils."""

from repoze.workflow import get_workflow

# Marker object for checking if key parameter was passed
sentinel = object()


class GetByIdMixin(object):
    """A mixin for adding by_id method to models."""

    @classmethod
    def by_id(cls, id, default=sentinel):
        """Get a Model object by id."""
        try:
            id = int(id)
            return cls.query.filter_by(id=id).first()
        except (ValueError, TypeError) as exc:
            if default == sentinel:
                raise exc
            else:
                return default


class GetByNameMixin(object):
    """A mixin for adding by_name method to models."""

    @classmethod
    def by_name(cls, name, default=sentinel):
        """Get a Model object by name."""
        try:
            str(name).decode('ascii')
            return cls.query.filter_by(name=name).first()
        except UnicodeDecodeError as exc:
            if default == sentinel:
                raise exc
            else:
                return default


class WorkflowMixin(object):
    """A mixin for adding repoze.workflow support to models."""

    def to_state(self, to_state, workflow='status', request=None):
        """Transition to selected state.

        By default, it uses the ``status`` workflow. If you want to transition
        some other workflow, pass its name in the ``workflow`` argument.

        If you want to use a ``permission_checker`` you need to set the
        ``request`` parameter. Otherwise, None is OK.
        """
        wf = get_workflow(self.__class__, workflow)
        wf.transition_to_state(self, request, to_state)


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
