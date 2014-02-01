# -*- coding: utf-8 -*-
"""List, add, edit, remove and disable/enable portlets views."""

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import PortletPositions
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import FormView


@view_defaults(permission='admin')
class PortletView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        app_assets.need()

    @view_config(
        route_name='portlet_list',
        layout='default',
        renderer='pyramid_bimt:templates/portlets.pt',
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        table_assets.need()

        return {
            'positions': PortletPositions,
            'portlets': Portlet.query.order_by(
                Portlet.position, Portlet.weight.desc()).all(),
        }


@view_config(
    route_name='portlet_add',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class PortletAdd(FormView):
    buttons = ('submit', )
    title = 'Add Portlet'
    form_options = (('formid', 'portlet-add'), ('method', 'POST'))
    sqla_schema_class = Portlet
    sqla_fields = [
        'name',
        'position',
        'weight',
        'html',
    ]

    def after_schema(self, schema):
        self.inject_relationship_field(
            schema=schema, model=Group, before='position')

    def submit_success(self, appstruct):
        portlet = Portlet(
            name=appstruct['name'],
            groups=[Group.by_id(group_id) for group_id in appstruct['groups']],
            position=appstruct['position'],
            weight=appstruct['weight'],
            html=appstruct['html'],
        )

        Session.add(portlet)
        Session.flush()
        self.request.session.flash(u'Portlet "{}" added.'.format(portlet.name))
        return HTTPFound(
            location=self.request.route_path(
                'portlet_edit', portlet_id=portlet.id))

    def appstruct(self):
        return {
            'name': self.request.params.get('name', ''),
            'groups': self.request.params.get('groups', []),
            'position': self.request.params.get('position', ''),
            'weight': self.request.params.get('weight', 0),
            'html': self.request.params.get('html', u''),
        }


@view_config(
    route_name='portlet_edit',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class PortletEdit(FormView):
    buttons = ('save', )
    title = 'Edit Portlet'
    form_options = (('formid', 'portlet-edit'), ('method', 'POST'))
    sqla_schema_class = Portlet
    sqla_fields = [
        'name',
        'position',
        'weight',
        'html',
    ]

    def after_schema(self, schema):
        self.inject_relationship_field(
            schema=schema, model=Group, before='position')

    def save_success(self, appstruct):
        portlet = self.request.context

        portlet.name = appstruct['name']
        portlet.groups = [Group.by_id(group_id) for group_id in appstruct['groups']]  # noqa
        portlet.position = appstruct['position']
        portlet.weight = appstruct['weight']
        portlet.html = appstruct['html']

        self.request.session.flash(
            u'Portlet "{}" modified.'.format(portlet.name))
        return HTTPFound(
            location=self.request.route_path(
                'portlet_edit', portlet_id=portlet.id))

    def appstruct(self):
        groups = self.request.context.groups or []
        return {
            'name': self.request.context.name or '',
            'groups': [str(g.id) for g in groups],
            'position': self.request.context.position or '',
            'weight': self.request.context.weight or 0,
            'html': self.request.context.html or u'',
        }
