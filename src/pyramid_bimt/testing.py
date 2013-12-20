# -*- coding: utf-8 -*-
"""Shared/common testing code."""

from sqlalchemy import create_engine
from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid_bimt.scripts.populate import add_audit_log_event_types
from pyramid_bimt.scripts.populate import add_groups
from pyramid_bimt.scripts.populate import add_users


def initTestingDB(auditlog_types=False, groups=False, users=False):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    if auditlog_types:
        add_audit_log_event_types()

    if groups:
        add_groups()

    if users:
        add_users()
