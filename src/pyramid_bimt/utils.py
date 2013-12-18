# -*- coding: utf-8 -*-

from ast import literal_eval

import os


def safe_eval(text):
    """Safely evaluate `text` argument.

    `text` can be evaluated to string, number,
    tuple, list, dict, boolean, and None.
    Function text.capitalize() is for lower case
    'false' or 'true' strings, it does not break anything.
    """

    try:
        return literal_eval(text.capitalize())
    except (ValueError, SyntaxError):
        return text


def expandvars_dict(settings):
    """Expands all environment variables in a settings dictionary."""

    return dict((key, safe_eval(os.path.expandvars(value))) for (key,
                value) in settings.iteritems())
