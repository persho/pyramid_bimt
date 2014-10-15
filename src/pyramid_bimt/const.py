# -*- coding: utf-8 -*-
"""Definitions of constant values."""

from flufl.enum import Enum


class Modes(Enum):
    development = 'development'
    testing = 'testing'
    production = 'production'


class BimtPermissions(Enum):
    view = 'View'
    manage = 'Manage'
    sudo = 'Super user'
