# -*- coding: utf-8 -*-
"""Define models."""

from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Unicode


class User(Base, BaseMixin):
    """A class representing a User."""

    __tablename__ = 'users'

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
        session = Session()
        result = session.query(User).filter_by(id=user_id)
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
