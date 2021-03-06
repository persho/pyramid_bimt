# -*- coding: utf-8 -*-
import os

PORT = os.environ.get('APP_PORT', 8080)
SELENIUM_IMPLICIT_WAIT = os.environ.get('SELENIUM_IMPLICIT_WAIT', '0.1s')
SELENIUM_TIMEOUT = os.environ.get('SELENIUM_IMPLICIT_WAIT', '20s')
APP_HOST = os.environ.get('APP_HOST', 'localhost')
APP_ADDR = os.environ.get('APP_URL', '{}:{}'.format(APP_HOST, PORT))
APP_URL = os.environ.get('APP_URL', 'http://{}'.format(APP_ADDR))
PHANTOMJS_ARGS = ['--ignore-ssl-errors=true', '--load-images=false']
MAIL_DIR = os.path.join(os.getcwd(), 'mail')

APP_NAME = os.environ.get('APP_NAME', 'pyramid_bimt')
