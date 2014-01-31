# -*- coding: utf-8 -*-
"""Miscellaneous helpers and tools views."""

from datetime import datetime
from pyramid.httpexceptions import exception_response
from pyramid.view import view_config
from pyramid_bimt.static import app_assets

import os


@view_config(
    route_name='raise_http_error',
    permission='admin',
)
def raise_http_error(request):
    raise exception_response(int(request.matchdict['error_code']))


@view_config(
    route_name='raise_js_error',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/form.pt',
)
def raise_js_error(request):
    app_assets.need()
    return {
        'title': 'JS error',
        'form': """<script type="text/javascript">
      throw new Error('[{now}] Error test.');
    </script>

    <p>[{now}] Error test.</p>""".format(now=datetime.utcnow())
    }


@view_config(
    route_name='config',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/config.pt',
)
def config(request):
    app_assets.need()
    request.layout_manager.layout.hide_sidebar = True
    settings = sorted(request.registry.settings.items(), key=lambda x: x[0])
    environ = sorted(os.environ.items(), key=lambda x: x[0])
    return {
        'title': 'Config',
        'environ': environ,
        'settings': settings,
        'secrets': [
            'BROKER_URL',
            'CELERY_RESULT_BACKEND',
            'authtkt.secret',
            'bimt.jvzoo_secret_key',
            'session.secret',
            'DATABASE_URL',
            'SENTRY_DSN',
        ]
    }
