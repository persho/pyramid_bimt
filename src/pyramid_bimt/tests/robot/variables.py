# -*- coding: utf-8 -*-
import os

PORT = os.environ.get('APP_PORT', 8080)
SELENIUM_IMPLICIT_WAIT = os.environ.get('SELENIUM_IMPLICIT_WAIT', '0.1s')
SELENIUM_TIMEOUT = os.environ.get('SELENIUM_IMPLICIT_WAIT', '20s')

APP_HOST = os.environ.get('APP_HOST', "localhost")
APP_ADDR = os.environ.get('APP_URL', "{}:{}".format(APP_HOST, PORT))
APP_URL = os.environ.get('APP_URL', "http://{}".format(APP_ADDR))
BROWSER = os.environ.get('BROWSER', "Firefox")
REMOTE_URL = os.environ.get('REMOTE_URL', "")
DESIRED_CAPABILITIES = os.environ.get('DESIRED_CAPABILITIES', "")

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '../../samples')
MAIL_DIR = os.path.join(os.getcwd(), '../../mail')
