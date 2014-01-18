# -*- coding: utf-8 -*-
"""Exceptions."""


class BIMTError(Exception):
    """Base class for all bms related exceptions."""


class WorkflowError(BIMTError):
    """Exception raised when disallowed workflow is used."""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
