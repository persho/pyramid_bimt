# -*- coding: utf-8 -*-
"""Definitions of constant values."""

from flufl.enum import Enum


class Modes(Enum):
    unknown = 'unknown'
    development = 'development'
    testing = 'testing'
    production = 'production'


class BimtPermissions(Enum):
    view = 'View'
    loginas = 'Login As'
    manage = 'Manage'
    sudo = 'Super user'
