# -*- coding: utf-8 -*-
"""Define models."""

from datetime import date
from datetime import datetime
from flufl.enum import Enum
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

import deform
import colander

_marker = object()


user_group_table = Table(
    'user_group',
    Base.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    UniqueConstraint('user_id', 'group_id', name='user_id_group_id'),
)


class Group(Base, BaseMixin):
    """A class representing a Group."""

    __tablename__ = 'groups'

    name = Column(
        String,
        unique=True,
    )

    @classmethod
    def by_name(self, name):
        return Group.query.filter(Group.name == name).first()


class UserProperty(Base, BaseMixin):
    """A key value store for user properties."""

    __tablename__ = 'user_properties'

    UniqueConstraint('key', 'user_id', name='key_user_id')

    #: unique for any key + user_id combination
    key = Column(
        String,
        unique=False,
        nullable=False,
    )

    #: value for the given key
    value = Column(Unicode)

    #: user id of the owner of this property
    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )


class User(Base, BaseMixin):
    """A class representing a User."""

    __tablename__ = 'users'

    #: shorthand for accessing user's groups
    groups = relationship(
        'Group', secondary=user_group_table, backref='users')

    #: shorthand for accessing user's auditlog entries
    audit_log_entries = relationship(
        'AuditLogEntry', backref='user')

    #: shorthand for accessing user's properties
    properties = relationship(
        'UserProperty', cascade='all,delete-orphan')

    #: used for logging in and system emails
    email = Column(
        String,
        unique=True,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Email',
        )}
    )

    #: encrypted with passlib
    password = Column(
        Unicode(120),
        nullable=True,
        info={'colanderalchemy': dict(
            title='Password',
            widget=deform.widget.PasswordWidget(size=128),
        )}
    )

    #: unicode fullname, used in UI and emails
    fullname = Column(
        Unicode(120),
        nullable=True,
        info={'colanderalchemy': dict(
            title='Full name',
        )}
    )

    #: email of the affiliate that referred this user
    affiliate = Column(
        Unicode,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Affiliate',
        )}
    )

    #: (optional) email that is used to make paypal purchases, if different
    #: than login email
    billing_email = Column(
        String,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Billing Email',
        )}
    )

    #: date until user's subscription is valid, after this date the
    #: :func:`expire_subscriptions
    #: <pyramid_bimt.scripts.expire_subscriptions.expire_subscriptions>` will
    #: disable the user
    valid_to = Column(
        Date,
        default=date.today,
        info={'colanderalchemy': dict(
            title='Valid To',
        )},
    )

    #: (optional) Date on which user made his latest payment
    last_payment = Column(
        Date,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Last payment',
        )},
    )

    def get_property(self, key, default=_marker):
        """TODO

        :param default: The return value if no property is found. Raises
            ValueError by default.
        :type default: anything
        """
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1:
            if default == _marker:
                raise ValueError(u'Cannot find property "{}".'.format(key))
            else:
                return default
        return result.one().value

    def set_property(self, key, value, strict=False):
        """TODO"""
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1 and strict:
            raise ValueError('Property "{}" not found.'.format(key))
        elif result.count() < 1 and not strict:
            self.properties.append(UserProperty(key=key, value=value))
        else:
            result.one().value = value

    @property
    def admin(self):
        """True if User is in 'admins' group, False otherwise."""
        return 'admins' in [g.name for g in self.groups]

    @property
    def enabled(self):
        """True if User is in 'enabled' group, False otherwise."""
        return 'enabled' in [g.name for g in self.groups]

    def enable(self):
        """Enable User by putting it in the 'enabled' group.

        :return: True if user was enabled, False if nothing changed.
        :rtype: bool
        """
        if not self.enabled:
            self.groups.append(Group.by_name('enabled'))
            return True
        else:
            return False

    def disable(self):
        """Disable User by removing it from the 'enabled' group.

        :return: True if user was disabled, False if nothing changed.
        :rtype: bool
        """
        if self.enabled:
            self.groups.remove(Group.by_name('enabled'))
            return True
        else:
            return False

    @property
    def trial(self):
        """True if User is in 'trial' group, False otherwise."""
        return 'trial' in [g.name for g in self.groups]

    @classmethod
    def by_id(self, user_id):
        """Get a User by id."""
        return User.query.filter_by(id=user_id).first()

    @classmethod
    def by_email(self, email):
        """Get a User by email."""
        return User.query.filter_by(email=email).first()

    @classmethod
    def by_billing_email(self, billing_email):
        """Get a User by billing email."""
        return User.query.filter_by(billing_email=billing_email).first()

    @classmethod
    def get_all(class_, order_by='email', filter_by=None, limit=1000):
        """Return all users.

        filter_by: dict -> {'name': 'foo'}

        By default, order by User.email.
        """
        User = class_
        q = User.query
        q = q.order_by(getattr(User, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q

    @classmethod
    def get_enabled(self):
        enabled = Group.by_name('enabled')
        return User.query.filter(User.groups.contains(enabled)).all()


class AuditLogEventType(Base):
    """A class representing an Audit log event type."""

    __tablename__ = 'audit_log_event_types'

    entries = relationship('AuditLogEntry', backref='event_type')

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
        return Session.query(AuditLogEventType).filter_by(name=name).first()

    @classmethod
    def by_id(self, id):
        """Get an auditlog event type by id.

        :param name: ID of the ``AuditLogEventType`` you want to get.
        :type name: int

        :return: ``AuditLogEventType`` object of the given id
        :rtype: instance of ``AuditLogEventType``
        """
        return Session.query(AuditLogEventType).filter_by(id=id).first()

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
def users_choice_widget(node, kw):
    users = User.get_all()
    choices = [(user.id, user.email) for user in users]
    return deform.widget.SelectWidget(values=choices)


@colander.deferred
def event_types_choice_widget(node, kw):
    types = AuditLogEventType.get_all()
    choices = [(type_.id, type_.name) for type_ in types]
    return deform.widget.SelectWidget(values=choices)


class AuditLogEntry(Base):
    __tablename__ = 'audit_log_entries'

    id = Column(
        Integer,
        primary_key=True,
    )

    #: when was the entry triggered
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        info={'colanderalchemy': dict(title='Timestamp')}
    )

    #: id of user that triggered the entry
    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        info={'colanderalchemy': dict(
            title='User ID',
            # TODO: Make values dynamic, not read at startup
            widget=users_choice_widget,
        )}
    )

    #: entry AuditLogEventType id
    event_type_id = Column(
        Integer,
        ForeignKey('audit_log_event_types.id'),
        info={'colanderalchemy': dict(
            title='Event Type ID',
            # TODO: Make values dynamic, not read at startup
            widget=event_types_choice_widget
        )}
    )

    #: (optional) additional information about the entry
    comment = Column(
        Unicode,
        info={'colanderalchemy': dict(
            title='Comment',
            missing=u'Manual audit log entry',
        )}
    )

    @classmethod
    def by_id(self, id):
        """Get an AuditLogEntry by id."""
        return Session.query(AuditLogEntry).filter_by(id=id).first()

    @classmethod
    def get_all(class_, order_by='timestamp', filter_by=None, limit=100):
        """Return all auditlog entries.

        By default, order by ``timestamp`` and limit to ``100`` results.

        :param order_by: The column name that should be used for ordering
            results.
        :type order_by: string

        :param order_by: Mapping of query filters, for example
            ``{'comment': 'foo'}``
        :type order_by: dict

        :return: list of AuditLogEntry instances, wrapped in a SQLAlchemy Query
            object, so you can call ``.all()`` to convert to list, or append
            additional query parameters (such as ``.desc()`` for descending)
        :rtype: :class:sqlalchemy.orm.query.Query
        """
        AuditLogEntry = class_
        q = Session.query(AuditLogEntry)
        q = q.order_by(getattr(AuditLogEntry, order_by).desc())
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q


portlet_group_table = Table(
    'portlet_group',
    Base.metadata,
    Column(
        'portlet_id',
        Integer,
        ForeignKey('portlets.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    UniqueConstraint('portlet_id', 'group_id', name='portlet_id_group_id'),
)


class PortletPositions(Enum):
    """Supported positions for portlets"""

    #: display a portlet in the main content area, next to the sidebar, just
    #: before any othercontent
    above_content = 'Above Content'

    #: display a portlet in the sidebar column, below any other sidebar content
    below_sidebar = 'Below Sidebar'

    #: display a portlet in the footer row, full-width, before any other footer
    #: content
    above_footer = 'Above Footer'


class Portlet(Base, BaseMixin):
    """A class representing a Portlet."""

    __tablename__ = 'portlets'

    name = Column(String, unique=True)

    html = Column(Unicode, default=u'')

    groups = relationship(
        'Group', secondary=portlet_group_table, backref='portlets')

    position = Column(String)

    weight = Column(Integer, default=0)

    @property
    def enabled(self):
        """True if Portlet is in any of the groups, False otherwise."""
        return len(self.groups) > 0

    @classmethod
    def by_id(self, portlet_id):
        """Get a Portlet by id."""
        return Portlet.query.filter_by(id=portlet_id).first()

    @classmethod
    def by_user_and_position(self, user, position):
        """Get all portlets that are visible to a user."""
        portlets = Portlet.query.filter(Portlet.position == position) \
            .order_by(Portlet.weight.desc())

        def any_group(groups1, groups2):
            for group1 in groups1:
                if group1 in groups2:
                    return True
            return False
        return [p for p in portlets if any_group(user.groups, p.groups)]

    @classmethod
    def get_all(class_, order_by='position', filter_by=None, limit=100):
        """Return all Portlets.

        filter_by: dict -> {'name': 'foo'}

        By default, order by Portlet.position.
        """
        Portlet = class_
        q = Portlet.query
        q = q.order_by(getattr(Portlet, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q.all()
