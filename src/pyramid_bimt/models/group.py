# -*- coding: utf-8 -*-
"""Group models."""

from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship


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

_marker = object()


class GroupProperty(Base, BaseMixin):
    """A key value store for group properties."""

    __tablename__ = 'group_properties'
    __table_args__ = (
        UniqueConstraint('key', 'group_id', name='key_group_id'),
    )

    #: unique for any key + group_id combination
    key = Column(
        String,
        unique=False,
        nullable=False,
    )

    #: value for the given key
    value = Column(Unicode)

    #: group id of the owner of this property
    group_id = Column(
        Integer,
        ForeignKey('groups.id'),
        nullable=False
    )

    def __repr__(self):
        """Custom representation of the GroupProperty object."""
        return u'<{}:{} (key={}, value={})>'.format(
            self.__class__.__name__, self.id, repr(self.key), repr(self.value))


class Group(Base, BaseMixin):
    """A class representing a Group."""

    __tablename__ = 'groups'

    @property
    def __acl__(self):
        # only admins can manage admins
        if self.name == 'admins':
            return [
                (Allow, 'g:admins', ALL_PERMISSIONS),
                DENY_ALL,
            ]
        return []  # traverse to GroupFactory's acl

    name = Column(
        String,
        unique=True,
    )

    product_id = Column(
        String,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='IPN Product ID',
            description='If this group is tied to a IPN product, enter its '
            'ID here. A single user can be a member of only one "product '
            'group" -- a group with product_id set.'
        )},
    )

    validity = Column(
        Integer,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Validity Days',
            description='Number of days to extend valid_to when a user from '
            'this group makes a payment',
        )},
    )

    trial_validity = Column(
        Integer,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Validity Days for Trial',
            description='If greater than "0" then members of this group will '
            'first be put in the trial group and their valid_to will be set '
            'to this amount of days in the future.',
        )},
    )

    forward_ipn_to_url = Column(
        String,
        nullable=True,
        info={'colanderalchemy': dict(
            title='IPN request redirect URL',
            description='When the app gets an Instant payment notification '
            'from JVZoo or Clickbank, if this field is not empty, it '
            're-posts the IPN POST request to the specified URL.'
        )},
    )

    #: shorthand for accessing group's properties
    properties = relationship(
        'GroupProperty', cascade='all,delete-orphan')

    def __repr__(self):
        """Custom representation of the Group object."""
        return u'<{}:{} (name={})>'.format(
            self.__class__.__name__, self.id, repr(self.name))

    def get_property(self, key, default=_marker):
        """Get a Group's property by key.

        :param key: Key by which to find the property.
        :type key: Unicode
        :param default: The return value if no property is found. Raises
            ValueError by default.
        :type default: anything
        :return: value of the property
        :rtype: Unicode
        """
        result = GroupProperty.query.filter_by(group_id=self.id, key=key)
        if result.count() < 1:
            if default == _marker:
                raise KeyError(u'Property "{}" not found.'.format(key))
            else:
                return default
        return result.one().value

    def set_property(self, key, value, strict=False):
        """Set a Group's property by key.

        :param key: Key by which to save the property.
        :type key: Unicode
        :param value: Value of the property.
        :type value: Unicode
        :param strict: If True, raise an error if property of given key key
            does not yet exists. In other words, update an existing property or
            fail. False by default.
        :type strict: bool
        """
        result = GroupProperty.query.filter_by(group_id=self.id, key=key)
        if result.count() < 1 and strict:
            raise KeyError('Property "{}" not found.'.format(key))
        elif result.count() < 1 and not strict:
            self.properties.append(GroupProperty(key=key, value=value))
        else:
            result.one().value = value

    @classmethod
    def by_id(self, group_id):
        """Get a Group by id."""
        return Group.query.filter_by(id=group_id).first()

    @classmethod
    def by_name(self, name):
        """Get a Group by name."""
        return Group.query.filter_by(name=name).first()

    @classmethod
    def by_product_id(self, product_id):
        """Get a Group by product_id."""
        return Group.query.filter_by(product_id=product_id).first()

    @classmethod
    def get_all(class_, order_by='name', filter_by=None, limit=None):
        """Return all groups.

        filter_by: dict -> {'name': 'foo'}

        By default, order by Group.name.
        """
        Group = class_
        q = Group.query
        q = q.order_by(getattr(Group, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        if limit:
            q = q.limit(limit)
        return q
