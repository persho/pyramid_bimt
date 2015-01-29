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


class AttrDict(dict):
    """Dict with support for attribute access."""
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def flatten(d):
    """Flatten a nested dict into a one-level dict, fullstop-delimited."""
    def items():
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subvalue in flatten(value).items():
                    yield key + '.' + subkey, subvalue
            if isinstance(value, list):
                for index, item in enumerate(value):
                    for subkey, subvalue in flatten(item).items():
                        yield key + '.{}.'.format(index) + subkey, subvalue
            else:
                yield key, value

    return dict(items())
