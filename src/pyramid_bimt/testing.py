# -*- coding: utf-8 -*-
"""Shared/common testing code."""

from sqlalchemy import create_engine
from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid_bimt.scripts.populate import add_default_content


def initTestingDB(empty=False):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    if not empty:
        add_default_content()
