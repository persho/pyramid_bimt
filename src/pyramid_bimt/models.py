# -*- coding: utf-8 -*-
"""Define models."""

from datetime import datetime
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from sqlalchemy import Column
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
    def get(self, name):
        group = Session.query(Group).filter(Group.name == name).one()
        return group


class UserProperty(Base, BaseMixin):
    """A key value store for user properties."""

    __tablename__ = 'user_properties'

    key = Column(
        String,
        unique=True,
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
    properties = relationship(
        "UserProperty",
        cascade="all,delete-orphan",
    )

    def get_property(self, key):
        result = Session.query(UserProperty).filter_by(user_id=self.id, key=key)
        if result.count() < 1:
            return None
        return result.one().value

    def set_property(self, key, value, strict=False):
        result = Session.query(UserProperty).filter_by(user_id=self.id, key=key)
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
            users = Group.get('users')
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
            users = Group.get('users')
            self.groups.remove(users)
            return True
        else:
            return False

    @classmethod
    def get(self, email):
        """Get a User by email."""
        result = Session.query(User).filter_by(email=email)
        if result.count() < 1:
            return None
        return result.one()

    @classmethod
    def get_by_id(self, user_id):
        """Get a User by id."""
        result = Session.query(User).filter_by(id=user_id)
        if result.count() < 1:
            return None
        return result.one()

    @classmethod
    def get_all(class_, order_by='email', filter_by=None, limit=1000):
        """Return all users.

        filter_by: dict -> {'name': 'foo'}

        By default, order by User.email.
        """
        User = class_
        q = Session.query(User)
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
    def get(self, name):
        """Get an AuditLogEventType by name."""
        result = Session.query(AuditLogEventType).filter_by(name=name)
        if result.count() < 1:
            return None
        return result.one()

    @classmethod
    def get_by_id(self, id):
        """Get an AuditLogEventType by id."""
        result = Session.query(AuditLogEventType).filter_by(id=id)
        if result.count() < 1:
            return None
        return result.one()

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
    def get(self, id):
        """Get an AuditLogEntry by id."""
        result = Session.query(AuditLogEntry).filter_by(id=id)
        if result.count() < 1:
            return None
        return result.one()

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
