# -*- coding: utf-8 -*-
"""Python keyword for reloading database"""

from bas.testing import initTestingDB
from pyramid_basemodel import Base

import transaction


class ReloadDB:

    def init_db(self):
        with transaction.manager:
            Base.metadata.drop_all()
            Base.metadata.create_all()
            initTestingDB(skip_bind=True)
