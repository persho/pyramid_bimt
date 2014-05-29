# -*- coding: utf-8 -*-
"""Python keyword for reloading database"""
from pyramid_basemodel import Base

import transaction


class ReloadDB:

    def init_db(self, args):
        """Method that resets the DB for each test"""
        app = __import__(args)
        with transaction.manager:
            Base.metadata.drop_all()
            Base.metadata.create_all()
            app.testing.initTestingDB(skip_bind=True)
