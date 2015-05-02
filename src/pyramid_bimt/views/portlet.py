# -*- coding: utf-8 -*-
"""List, add, edit, remove and disable/enable portlets views."""

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.models import Group
from pyramid_bimt.models import Portlet
from pyramid_bimt.models import PortletPositions
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import chosen_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import FormView
from pyramid_bimt.views import SQLAlchemySchemaNode

import colander
import deform


@view_defaults(permission=BimtPermissions.manage)
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
        self.request.layout_manager.layout.title = u'Portlets'
        table_assets.need()

        return {
            'positions': PortletPositions,
            'portlets': Portlet.query.order_by(
                Portlet.position, Portlet.weight.desc()).all(),
        }


@view_config(
    route_name='portlet_add',
    layout='default',
    permission=BimtPermissions.manage,
    renderer='pyramid_bimt:templates/form.pt',
)
class PortletAdd(FormView):
    buttons = ('submit', )
    title = 'Add Portlet'
    form_options = (('formid', 'portlet-add'), ('method', 'POST'))
    fields = [
        'name',
        'position',
        'weight',
        'html',
    ]

    def __init__(self, request):
        chosen_assets.need()

        self.request = request
        self.schema = SQLAlchemySchemaNode(Portlet, includes=self.fields)

        # we don't like the way ColanderAlchemy renders SA Relationships so
        # we manually inject a suitable SchemaNode for groups
        choices = [(group.id, group.name) for group in Group.get_all()]
        self.schema.add_before(
            'position',
            node=colander.SchemaNode(
                colander.Set(),
                name='groups',
                missing=[],
                widget=deform.widget.CheckboxChoiceWidget(values=choices),
            ),
        )
        self.schema.add_before(
            'position',
            node=colander.SchemaNode(
                colander.Set(),
                name='exclude_groups',
                missing=[],
                widget=deform.widget.CheckboxChoiceWidget(values=choices),
            ),
        )

    def submit_success(self, appstruct):
        portlet = Portlet(
            name=appstruct.get('name'),
            groups=[Group.by_id(group_id) for group_id in appstruct.get('groups')],  # noqa
            exclude_groups=[Group.by_id(group_id) for group_id in appstruct.get('exclude_groups')],  # noqa
            position=appstruct.get('position'),
            weight=appstruct.get('weight'),
            html=appstruct.get('html'),
        )

        Session.add(portlet)
        Session.flush()
        self.request.session.flash(u'Portlet "{}" added.'.format(portlet.name))
        return HTTPFound(
            location=self.request.route_path(
                'portlet_edit', portlet_id=portlet.id))

    def appstruct(self):
        appstruct = dict()
        for field in self.fields + ['groups', 'exclude_groups']:
            if self.request.params.get(field) is not None:
                appstruct[field] = self.request.params[field]

        return appstruct


@view_config(
    route_name='portlet_edit',
    layout='default',
    permission=BimtPermissions.manage,
    renderer='pyramid_bimt:templates/form.pt',
)
class PortletEdit(PortletAdd):
    buttons = ('save', )
    title = 'Edit Portlet'
    form_options = (('formid', 'portlet-edit'), ('method', 'POST'))

    def save_success(self, appstruct):
        portlet = self.request.context

        portlet.name = appstruct['name']
        portlet.groups = [Group.by_id(group_id) for group_id in appstruct['groups']]  # noqa
        portlet.exclude_groups = [Group.by_id(group_id) for group_id in appstruct['exclude_groups']]  # noqa
        portlet.position = appstruct['position']
        portlet.weight = appstruct['weight']
        portlet.html = appstruct['html']

        self.request.session.flash(
            u'Portlet "{}" modified.'.format(portlet.name))
        return HTTPFound(
            location=self.request.route_path(
                'portlet_edit', portlet_id=portlet.id))

    def appstruct(self):
        context = self.request.context
        appstruct = dict()
        for field in self.fields:
            if (
                hasattr(context, field) and
                getattr(context, field) is not None
            ):
                appstruct[field] = getattr(context, field)

        if context.groups:
            appstruct['groups'] = [str(g.id) for g in context.groups]
        if context.exclude_groups:
            appstruct['exclude_groups'] = [str(g.id) for g in context.exclude_groups]  # noqa
        return appstruct
