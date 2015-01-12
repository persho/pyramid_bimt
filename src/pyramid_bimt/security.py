# -*- coding: utf-8 -*-
"""Security-aware methods."""

from Crypto import Random
from Crypto.Cipher import AES
from passlib.apps import custom_app_context as pwd_context
from passlib.utils import generate_password
from pyramid.threadlocal import get_current_registry

import base64
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


class SymmetricEncryption(object):
    BS = 16

    def __init__(self):
        self.key = get_current_registry().settings['bimt.encryption_aes_16b_key']  # noqa

    def _pad(self, s):
        return s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS)  # noqa

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

    def encrypt(self, s):
        s = self._pad(s)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(s))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[16:]))
