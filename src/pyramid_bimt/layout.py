# -*- coding: utf-8 -*-
"""Default layout for BIMT apss. Every app can roll its own if needed."""

from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config

import os


@layout_config(name='default', template='templates/default_layout.pt')
class DefaultLayout(object):
    page_title = 'BIMT App'

    def __init__(
        self,
        context,
        request,
        current_page='Home',
        hide_sidebar=False,
    ):
        self.context = context
        self.request = request
        self.current_page = current_page
        self.hide_sidebar = hide_sidebar
        self.app_title = self.request.registry.settings['bimt.app_title']

    def sentry_dsn(self):
        return "SENTRY_DSN" in os.environ


@panel_config(name='footer')
def footer(context, request):
    return 'Footer placeholder'


@panel_config(name='navbar')
def navbar(context, request):
    return 'navbar placeholder'


@panel_config(name='sidebar')
def sidebar(context, request):
    return 'sidebar placeholder'
