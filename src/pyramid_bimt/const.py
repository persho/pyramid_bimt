# -*- coding: utf-8 -*-
"""Definitions of constant values."""

from flufl.enum import Enum


class BimtPermissions(Enum):
    view = 'View'
    manage = 'Manage'
    sudo = 'Super user'
