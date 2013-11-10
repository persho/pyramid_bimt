# -*- coding: utf-8 -*-
"""Default layout for BIMT apss. Every app can roll its own if needed."""

from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config


@layout_config(name='default', template='templates/default_layout.pt')
class DefaultLayout(object):
    page_title = 'BIMT App'

    def __init__(self, context, request, app_name='BIMT', current_page='Home'):
        self.context = context
        self.request = request
        self.app_name = app_name
        self.current_page = current_page


@panel_config(name='footer')
def footer(context, request):
    return 'Footer placeholder'


@panel_config(name='navbar')
def navbar(context, request):
    return 'navbar placeholder'


@panel_config(name='sidebar')
def sidebar(context, request):
    return 'sidebar placeholder'
