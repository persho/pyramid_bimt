# -*- coding: utf-8 -*-
"""Find users with expired `valid_to` and disable them."""

from datetime import date
from pyramid_basemodel import Session
from pyramid_bimt.models import User
from sqlalchemy import engine_from_config

import logging
import os
import sys
import transaction

logger = logging.getLogger(__name__)


def expire_subscriptions():
    with transaction.manager:
        for user in User.get_all():
            if user.enabled:
                if user.valid_to < date.today():
                    user.disable()
                    logger.info(
                        "Disabled user {} because its valid_to ({}) has "
                        "expired.".format(user.id, user.valid_to))


def main(argv=sys.argv):

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise KeyError("DATABASE_URL not set, please set it.")

    settings = {'sqlalchemy.url': db_url}
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    expire_subscriptions()
    print "Expire subscription script finished."


if __name__ == '__main__':
    main()
