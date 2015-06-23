# -*- coding: utf-8 -*-
"""User models."""

from .group import Group
from .group import user_group_table
from datetime import date
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from pyramid_bimt.models import GetByIdMixin
from pyramid_bimt.security import SymmetricEncryption
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy import or_
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

import colander
import deform

_marker = object()


class UserProperty(Base, BaseMixin):
    """A key value store for user properties."""

    __tablename__ = 'user_properties'
    __table_args__ = (
        UniqueConstraint('key', 'user_id', name='key_user_id'),
    )

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


class User(Base, BaseMixin, GetByIdMixin):
    """A class representing a User."""

    __tablename__ = 'users'

    @property
    def __acl__(self):
        # only admins can manage admins
        if self.admin:
            return [
                (Allow, 'g:admins', ALL_PERMISSIONS),
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
        Unicode(120),
        info={'colanderalchemy': dict(
            title='Affiliate',
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

    def has_property(self, key):
        """True if user has this property set."""
        prop = UserProperty.query.filter_by(user_id=self.id, key=key).first()
        if prop:
            return True
        return False

    def get_property(self, key, default=_marker, secure=False):
        """Get a User's property by key.

        :param key: Key by which to find the property.
        :type key: Unicode
        :param default: The return value if no property is found. Raises
            ValueError by default.
        :type default: anything
        :param secure: Symetrically encrypt the property before storing to DB.
        :type secure: bool
        :return: Value of the property.
        :rtype: Unicode
        """
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1:
            if default == _marker:
                raise KeyError(u'Property "{}" not found.'.format(key))
            else:
                return default
        value = result.one().value
        if secure:
            return SymmetricEncryption().decrypt(value)
        else:
            return value

    def set_property(self, key, value, strict=False, secure=False):
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
        if secure:
            value = unicode(SymmetricEncryption().encrypt(value))
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
    def product_group(self):
        """Get the user's group that has product_id set. Can be only one.

        Groups with group.addon set to True are ignored.
        """
        try:
            return Group.query\
                .filter(Group.users.contains(self))\
                .filter(Group.addon == False)\
                .filter(Group.product_id != None).one()  # noqa
        except NoResultFound:
                return None

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
    def by_email(self, email):
        """Get a User by email."""
        return User.query.filter_by(email=email).first()

    @classmethod
    def by_billing_email(self, billing_email):
        """Get a User by billing email."""
        return User.query.filter_by(billing_email=billing_email).first()

    @classmethod
    def get_all(
        class_,
        order_by='email',
        order_direction='asc',
        filter_by=None,
        offset=None,
        search=None,
        limit=None,
        request=None,
        security=None,
    ):
        """Return all users.

        filter_by: dict -> {'name': 'foo'}

        By default, order by User.email.
        """
        User = class_
        q = Session.query(User)
        # Set correct order_by for timestamps
        if order_by == 'modified':
            order_by = 'm'
        elif order_by == 'created':
            order_by = 'c'
        q = q.order_by('{} {}'.format(order_by, order_direction))
        if filter_by:
            q = q.filter_by(**filter_by)
        if search:
            q = q.filter(or_(
                User.email.ilike(u'%{}%'.format(search)),
                User.fullname.ilike(u'%{}%'.format(search)),
            ))
        if offset:
            q = q.slice(offset[0], offset[1])
        elif limit:
            q = q.limit(limit)
        return q

    @classmethod
    def get_enabled(self):
        enabled = Group.by_name('enabled')
        return User.query.filter(User.groups.contains(enabled)).all()
