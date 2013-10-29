# -*- coding: utf-8 -*-
"""Security-aware methods."""

from passlib.apps import custom_app_context as pwd_context


def encrypt(raw_password):
    """Encrypt a raw password into a secure hash using passlib."""
    v = raw_password.strip()
    s = pwd_context.encrypt(v, scheme="sha512_crypt", rounds=90000)
    return unicode(s)


def verify(raw_password, candidate_password):
    """Verify a password using passlib."""
    return pwd_context.verify(raw_password, candidate_password)
