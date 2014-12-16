# -*- coding: utf-8 -*-
"""AuditLog models."""

from datetime import datetime
from pyramid.security import Allow
from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.models import GetByIdMixin
from pyramid_bimt.models import GetByNameMixin
from pyramid_bimt.models.user import User
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy.orm import relationship

import colander
import deform


class AuditLogEventType(Base, GetByIdMixin, GetByNameMixin):
    """A class representing an Audit log event type."""

    __tablename__ = 'audit_log_event_types'

    entries = relationship('AuditLogEntry', backref='event_type')

    query = Session.query_property()

    id = Column(
        Integer,
        primary_key=True,
    )

    #: string, name of the event type
    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    #: unicode, for UI display
    title = Column(
        Unicode,
    )

    #: unicode, for UI display
    description = Column(
        Unicode,
    )

    def __repr__(self):
        """Custom representation of the AuditLogEventType object."""
        return u'<{}:{} (name={})>'.format(
            self.__class__.__name__, self.id, repr(self.name))

    @classmethod
    def by_name(self, name):
        """Get an auditlog event type by name.

        A convenience method for getting an ``AuditLogEventType`` by name.
        Normally you need this when adding a new :class:`AuditLogEntry
        <pyramid_bimt.models.AuditLogEntry>` and you need to set its
        :attr:`event type <pyramid_bimt.models.AuditLogEntry.event_type_id>`:

        .. code-block:: python

            AuditLogEntry(
                user_id=user.id,
                event_type_id=AuditLogEventType.by_name('UserEnabled').id,
            )

        :param name: Name of the ``AuditLogEventType`` you want to get.
        :type name: string

        :return: ``AuditLogEventType`` object of the given name
        :rtype: instance of ``AuditLogEventType``
        """
        return super(AuditLogEventType, self).by_name(name)

    @classmethod
    def get_all(class_, order_by='name', filter_by=None, limit=100):
        """Return all auditlog event types.

        :param order_by: The column name that should be used for ordering
            results.
        :type order_by: string

        :param filter_by: Mapping of query filters, for example
            ``{'description': 'foo'}``
        :type filter_by: dict

        :return: list of AuditLogEventType instances, wrapped in a SQLAlchemy
            Query object, so you can call ``.all()`` to convert to list, or
            append additional query parameters (such as ``.desc()`` for
            descending)
        :rtype: :class:sqlalchemy.orm.query.Query
        """
        AuditLogEventType = class_
        q = Session.query(AuditLogEventType)
        q = q.order_by(getattr(AuditLogEventType, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q


@colander.deferred
def users_select_widget(node, kw):
    users = User.get_all()
    choices = [(user.id, user.email) for user in users]
    return deform.widget.SelectWidget(values=choices)


@colander.deferred
def event_types_select_widget(node, kw):
    types = AuditLogEventType.get_all()
    choices = [(type_.id, type_.name) for type_ in types]
    return deform.widget.SelectWidget(values=choices)


class AuditLogEntry(Base, GetByIdMixin):
    __tablename__ = 'audit_log_entries'

    @property
    def __acl__(self):
        return [  # pragma: no cover
            (Allow, self.user.email, BimtPermissions.manage),
        ]

    query = Session.query_property()

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        info={'colanderalchemy': dict(
            title='User ID',
            description='ID of user that triggered the entry.',
            widget=users_select_widget,
        )}
    )

    event_type_id = Column(
        Integer,
        ForeignKey('audit_log_event_types.id'),
        info={'colanderalchemy': dict(
            title='Event Type ID',
            widget=event_types_select_widget
        )}
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        info={'colanderalchemy': dict(
            title='Timestamp',
            description='When was the entry triggered.',
        )}
    )

    comment = Column(
        Unicode,
        info={'colanderalchemy': dict(
            title='Comment',
            description='Optional additional information about the entry.',
            missing=u'Manual audit log entry',
        )}
    )

    read = Column(
        Boolean,
        default=False,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Read',
            description=u'True if this entry has been read, False if not.',
        )}
    )

    def __repr__(self):
        """Custom representation of the AuditLogEntry object."""
        user = self.user and self.user.email or None
        event_type = self.event_type and self.event_type.name or None
        return u'<{}:{} (user={}, type={})>'.format(
            self.__class__.__name__, self.id, repr(user), repr(event_type))

    @classmethod
    def get_all(
        class_,
        request=None,
        order_by='timestamp',
        order_direction='desc',
        filter_by=None,
        offset=None,
        search=None,
        limit=None,
        security=True,
    ):
        """Return all auditlog entries.

        By default, order descending by ``timestamp`` and limit to ``100``
        results.

        :param order_by: The column name that should be used for ordering
            results.
        :type order_by: string

        :param order_direction: Name of order direction: 'asc' or 'desc'.
        :type order_direction: string

        :param filter_by: Mapping of query filters, for example
            ``{'comment': 'foo'}``
        :type filter_by: dict

        :param security: Only return entries that the current user is owner of.
        :type security: bool

        :return: list of AuditLogEntry instances, wrapped in a SQLAlchemy Query
            object, so you can call ``.all()`` to convert to list, or append
            additional query parameters (such as ``.count()`` for counting)
        :rtype: :class:sqlalchemy.orm.query.Query
        """
        if security and not request:
            raise KeyError('You must provide request when security is True!')
        AuditLogEntry = class_
        q = Session.query(AuditLogEntry)
        q = q.order_by('{} {}'.format(order_by, order_direction))
        if filter_by:
            q = q.filter_by(**filter_by)
        if search:
            q = q.filter(AuditLogEntry.comment.like(u'%{}%'.format(search)))
        if security:
            q = q.filter_by(user=request.user)
        if offset:
            q = q.slice(offset[0], offset[1])
        elif limit:
            q = q.limit(limit)
        return q
