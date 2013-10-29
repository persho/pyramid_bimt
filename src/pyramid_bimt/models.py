# -*- coding: utf-8 -*-
"""Define models."""

from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
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


class User(Base, BaseMixin):
    """A class representing a User."""

    __tablename__ = 'users'

    groups = relationship(
        'Group', secondary=user_group_table, backref='users')

    email = Column(
        String,
        unique=True,
        nullable=False,
    )
    password = Column(
        Unicode(120),
        nullable=False,
    )

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
    def get_all(class_, order_by='email', filter_by=None):
        """Return all users.

        filter_by: dict -> {'name': 'foo'}

        By default, order by User.email.
        """
        User = class_
        q = Session.query(User)
        q = q.order_by(getattr(User, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        return q
