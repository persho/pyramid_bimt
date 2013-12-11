# -*- coding: utf-8 -*-
"""Security-aware methods."""

from passlib.apps import custom_app_context as pwd_context
from passlib.utils import generate_password

import logging

logger = logging.getLogger(__name__)


def encrypt(cleartext):
    """Encrypt a raw password into a secure salted hash using passlib."""
    cleartext = cleartext.strip()
    cyphertext = pwd_context.encrypt(
        cleartext,
        scheme='sha512_crypt',
        rounds=90000,
    )
    return unicode(cyphertext)


def verify(cleartext, cyphertext):
    """Verify a password using passlib."""
    try:
        return pwd_context.verify(cleartext, cyphertext)
    except Exception as e:
        logger.exception(e)
        return False


def generate(**kwargs):
    """Generate a secure password."""
    return generate_password(**kwargs)
