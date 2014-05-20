# -*- coding: utf-8 -*-
"""Group models."""

from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import UniqueConstraint


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

    product_id = Column(
        Integer,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='JVZoo Product ID',
            description='If this group is tied to a JVZoo product, enter its '
            'ID here.'
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
            title='JVZoo IPN request redirect URL',
            description='When the app gets an Instant payment notification '
            'from JVZoo, if this field is not empty, it redirects the request '
            'to the specified URL'
        )},
    )

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
    def get_all(class_, order_by='name', filter_by=None, limit=1000):
        """Return all groups.

        filter_by: dict -> {'name': 'foo'}

        By default, order by Group.name.
        """
        Group = class_
        q = Group.query
        q = q.order_by(getattr(Group, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q
