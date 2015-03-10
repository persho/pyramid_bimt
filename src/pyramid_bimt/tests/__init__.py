# -*- coding: utf-8 -*-
"""Tests initializer."""
import sqlalchemy
import warnings

# Only throw errors for SAWarnings not related to sqlite
warnings.filterwarnings(
    'error',
    message='^(.(?!(sqlite)))*$',
    category=sqlalchemy.exc.SAWarning,
)
