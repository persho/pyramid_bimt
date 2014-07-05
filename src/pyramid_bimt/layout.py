# -*- coding: utf-8 -*-
"""Default layout for BIMT apps. Every app can roll its own if needed."""

from pyramid_bimt.models import Portlet
from pyramid_bimt.models import PortletPositions
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
        self.sentry_dsn = 'SENTRY_DSN' in os.environ

    def flash_messages(self):
        pop = self.request.session.pop_flash
        messages = []
        for queue in ('', 'info', 'warning', 'error'):
            for msg in pop(queue):
                if queue == '':
                    queue_ = 'info'
                elif queue == 'error':
                    queue_ = 'danger'
                else:
                    queue_ = queue
                messages.append(dict(msg=msg, level=queue_))
        return messages


@panel_config(name='footer')
def footer(context, request):
    return 'Footer placeholder'


@panel_config(name='navbar')
def navbar(context, request):
    return 'navbar placeholder'


@panel_config(name='sidebar')
def sidebar(context, request):
    return 'sidebar placeholder'


@panel_config(name='above_content_portlets')
def above_content_portlets(context, request):
    if request.user:
        portlets = Portlet.by_user_and_position(
            request.user, PortletPositions.above_content.name)
        if portlets:
            return render_portlets(portlets)
    return ''


@panel_config(name='below_sidebar_portlets')
def below_sidebar_portlets(context, request):
    if request.user:
        portlets = Portlet.by_user_and_position(
            request.user, PortletPositions.below_sidebar.name)
        if portlets:
            return render_portlets(portlets)
    return ''


@panel_config(name='above_footer_portlets')
def above_footer_portlets(context, request):
    if request.user:
        portlets = Portlet.by_user_and_position(
            request.user, PortletPositions.above_footer.name)
        if portlets:
            return render_portlets(portlets)
    return ''


def render_portlets(portlets):
    """Render selected portlets"""
    return u''.join([portlet.get_rendered_portlet() for portlet in portlets])
