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

    key = Column(
        String,
        unique=False,
        nullable=False,
    )
    value = Column(Unicode)

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )


class User(Base, BaseMixin):
    """A class representing a User."""

    __tablename__ = 'users'

    groups = relationship(
        'Group', secondary=user_group_table, backref='users')

    audit_log_entries = relationship(
        'AuditLogEntry', backref='user')

    properties = relationship(
        'UserProperty', cascade='all,delete-orphan')

    email = Column(
        String,
        unique=True,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Email',
        )}
    )
    password = Column(
        Unicode(120),
        nullable=True,
        info={'colanderalchemy': dict(
            title='Password',
            widget=deform.widget.PasswordWidget(size=128),
        )}
    )
    fullname = Column(
        Unicode(120),
        nullable=True,
        info={'colanderalchemy': dict(
            title='Full name',
        )}
    )
    affiliate = Column(
        Unicode,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Affiliate',
        )}
    )
    billing_email = Column(
        String,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Billing Email',
        )}
    )
    valid_to = Column(
        Date,
        default=date.today,
        info={'colanderalchemy': dict(
            title='Valid To',
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
        """True if User is in 'users' group, False otherwise."""
        return 'users' in [g.name for g in self.groups]

    def enable(self):
        """Enable User by putting it in the 'users' group.

        :return: True if user was enabled, False if nothing changed.
        :rtype: bool
        """
        if not self.enabled:
            users = Group.by_name('users')
            self.groups.append(users)
            return True
        else:
            return False

    def disable(self):
        """Disable User by removing it from the 'users' group.

        :return: True if user was disabled, False if nothing changed.
        :rtype: bool
        """
        if self.enabled:
            users = Group.by_name('users')
            self.groups.remove(users)
            return True
        else:
            return False

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


class AuditLogEventType(Base):
    """A class representing an Audit log event type."""

    __tablename__ = 'audit_log_event_types'

    entries = relationship('AuditLogEntry', backref='event_type')

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    title = Column(
        Unicode,
    )

    description = Column(
        Unicode,
    )

    @classmethod
    def by_name(self, name):
        """Get an AuditLogEventType by name."""
        return Session.query(AuditLogEventType).filter_by(name=name).first()

    @classmethod
    def by_id(self, id):
        """Get an AuditLogEventType by id."""
        return Session.query(AuditLogEventType).filter_by(id=id).first()

    @classmethod
    def get_all(class_, order_by='name', filter_by=None):
        """Return all Audit log event types.

        filter_by: dict -> {'name': 'foo'}

        By default, order by AuditLogEventType.name.
        """
        AuditLogEventType = class_
        q = Session.query(AuditLogEventType)
        q = q.order_by(getattr(AuditLogEventType, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
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
    """A class representing an Audit log entry."""

    __tablename__ = 'audit_log_entries'

    id = Column(
        Integer,
        primary_key=True,
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        info={'colanderalchemy': dict(title='Timestamp')}
    )

    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        info={'colanderalchemy': dict(
            title='User ID',
            # TODO: Make values dynamic, not read at startup
            widget=users_choice_widget,
        )}
    )

    event_type_id = Column(
        Integer,
        ForeignKey('audit_log_event_types.id'),
        info={'colanderalchemy': dict(
            title='Event Type ID',
            # TODO: Make values dynamic, not read at startup
            widget=event_types_choice_widget
        )}
    )

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
        """Return all Audit log entries.

        filter_by: dict -> {'name': 'foo'}

        By default, order by AuditLogEntry.AuditLogEventType.
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
    above_content = 'Above Content'
    below_sidebar = 'Below Sidebar'
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
