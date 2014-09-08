# -*- coding: utf-8 -*-
"""User models."""

from .group import Group
from .group import user_group_table
from datetime import date
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

import colander
import deform

_marker = object()


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

    def __repr__(self):
        """Custom representation of the UserProperty object."""
        return u'<{}:{} (key={}, value={})>'.format(
            self.__class__.__name__, self.id, repr(self.key), repr(self.value))


class User(Base, BaseMixin):
    """A class representing a User."""

    __tablename__ = 'users'

    @property
    def __acl__(self):
        # only admins can manage admins
        if self.admin:
            return [
                (Allow, 'g:admins', 'manage_users'),
                DENY_ALL,
            ]
        return []  # use UserFactory's acl

    #: used for logging in and system emails
    email = Column(
        String,
        unique=True,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Email',
            validator=colander.Email(),
        )}
    )

    #: encrypted with passlib
    password = Column(
        Unicode(120),
        info={'colanderalchemy': dict(
            title='Password',
            widget=deform.widget.PasswordWidget(size=128),
        )}
    )

    #: unicode fullname, used in UI and emails
    fullname = Column(
        Unicode(120),
        info={'colanderalchemy': dict(
            title='Full name',
        )}
    )

    #: email of the affiliate that referred this user
    affiliate = Column(
        Unicode,
        info={'colanderalchemy': dict(
            title='Affiliate',
            validator=colander.Email(),
        )}
    )

    #: (optional) email that is used to make paypal purchases, if different
    #: than login email
    billing_email = Column(
        String,
        unique=True,
        info={'colanderalchemy': dict(
            title='Billing Email',
            validator=colander.Email(),
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
        info={'colanderalchemy': dict(
            title='Last payment',
        )},
    )

    #: shorthand for accessing user's groups
    groups = relationship(
        'Group', secondary=user_group_table, backref='users')

    #: shorthand for accessing user's properties
    properties = relationship(
        'UserProperty', cascade='all,delete-orphan')

    #: shorthand for accessing user's auditlog entries
    audit_log_entries = relationship(
        'AuditLogEntry', backref='user')

    def __repr__(self):
        """Custom representation of the User object."""
        return u'<{}:{} (email={})>'.format(
            self.__class__.__name__, self.id, repr(self.email))

    def get_property(self, key, default=_marker):
        """Get a User's property by key.

        :param key: Key by which to find the property.
        :type key: Unicode
        :param default: The return value if no property is found. Raises
            ValueError by default.
        :type default: anything
        :return: value of the property
        :rtype: Unicode
        """
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1:
            if default == _marker:
                raise KeyError(u'Property "{}" not found.'.format(key))
            else:
                return default
        return result.one().value

    def set_property(self, key, value, strict=False):
        """Set a User's property by key.

        :param key: Key by which to save the property.
        :type key: Unicode
        :param value: Value of the property.
        :type value: Unicode
        :param strict: If True, raise an error if property of given key key
            does not yet exists. In other words, update an existing property or
            fail. False by default.
        :type strict: bool
        """
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1 and strict:
            raise KeyError('Property "{}" not found.'.format(key))
        elif result.count() < 1 and not strict:
            self.properties.append(UserProperty(key=key, value=value))
        else:
            result.one().value = value

    @property
    def admin(self):
        """True if User is in 'admins' group, False otherwise."""
        return 'admins' in [g.name for g in self.groups]

    @property
    def staff(self):
        """True if User is in 'staff' or 'admins' group, False otherwise."""
        return self.admin or 'staff' in [g.name for g in self.groups]

    @property
    def trial(self):
        """True if User is in 'trial' group, False otherwise."""
        return 'trial' in [g.name for g in self.groups]

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
    def unsubscribed(self):
        """True if User is in 'unsubscribed' group, False otherwise."""
        return 'unsubscribed' in [g.name for g in self.groups]

    def subscribe(self):
        """Subscribe User by removing it from the 'unsubscribed' group.

        :return: True if user was subscribed, False if nothing changed.
        :rtype: bool
        """
        if self.unsubscribed:
            self.groups.remove(Group.by_name('unsubscribed'))
            return True
        else:
            return False

    def unsubscribe(self):
        """Unsubscribed User by appending it from the 'unsubscribed' group.

        :return: True if user was unsubscribed, False if nothing changed.
        :rtype: bool
        """
        if self.unsubscribed:
            return False
        else:
            self.groups.append(Group.by_name('unsubscribed'))
            return True

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
