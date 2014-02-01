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
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView

import colander
import deform


class PortletSchema(colander.Schema):

    name = colander.SchemaNode(
        colander.String(),
        description='Enter Portlet Name',
        title='Name',
        validator=colander.Length(min=2, max=50),
        widget=deform.widget.TextInputWidget(),
    )

    groups = colander.SchemaNode(
        colander.Set(),
        description=u'Which user groups will see this portlet',
        title='Groups',
        widget=deform.widget.CheckboxChoiceWidget(
            values=[(g.name, g.name.capitalize()) for g in Group.query.all()]),
    )

    position = colander.SchemaNode(
        colander.String(),
        description=u'Position where portlet will be visible',
        title='Position',
        widget=deform.widget.RadioChoiceWidget(
            values=[(pos.name, pos.value) for pos in PortletPositions])
    )

    weight = colander.SchemaNode(
        colander.Integer(),
        default=0,
        description='The higher the number the higher portlet will be positioned (range from -128 to 127)',  # noqa
        title='Weight',
        validator=colander.Range(-128, 127)
    )

    html = colander.SchemaNode(
        colander.String(),
        description='Enter HTML code',
        title='HTML Code',
        validator=colander.Length(min=3),
        widget=deform.widget.TextAreaWidget(rows=10),
    )


@view_config(
    route_name='portlet_edit',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/form.pt',
)
class PortletEditForm(FormView):
    TITLE_EDIT = 'Edit Portlet'
    TITLE_ADD = 'Add Portlet'

    buttons = ('save', )
    title = TITLE_EDIT
    form_options = (('formid', 'portletedit'), ('method', 'POST'))
    schema = PortletSchema()

    def __call__(self):
        app_assets.need()
        form_assets.need()

        self.portlet = self.request.context
        if not self.portlet:
            self.title = self.TITLE_ADD

        self.request.layout_manager.layout.current_page = self.title

        result = super(PortletEditForm, self).__call__()
        if isinstance(result, dict):
            result['title'] = self.title
        return result

    def save_success(self, appstruct):
        if self.portlet:
            # edit portlet
            portlet = self.portlet
            portlet.name = appstruct['name']
            portlet.groups = [Group.by_name(name) for name in appstruct['groups']]  # noqa
            portlet.position = appstruct['position']
            portlet.weight = appstruct['weight']
            portlet.html = appstruct['html']
            self.request.session.flash(
                u'Portlet {} has been modified.'.format(portlet.id))
        else:
            # add portlet
            portlet = Portlet(
                name=appstruct['name'],
                groups=[Group.by_name(name) for name in appstruct['groups']],
                position=appstruct['position'],
                weight=appstruct['weight'],
                html=appstruct['html'],
            )
            Session.add(portlet)
            self.request.session.flash(
                u'Portlet {} has been added.'.format(portlet.id))

        Session.flush()  # this is needed, so that we get portlet.id NOW
        return HTTPFound(
            location=self.request.route_path('portlet_list'))

    def appstruct(self):
        params_groups = self.request.params.get('groups')
        if self.portlet and params_groups is None:
            groups = [
                g.name for g in self.portlet.groups
            ]
        else:
            groups = [g for g in params_groups or []]

        return {
            'name': self.request.params.get(
                'name', self.portlet.name if self.portlet else u''
            ),
            'html': self.request.params.get(
                'html', self.portlet.html if self.portlet else u''
            ),
            'position': self.request.params.get(
                'position',
                self.portlet.position if self.portlet else u''
            ),
            'groups': groups,
            'weight': self.request.params.get(
                'weight',
                self.portlet.weight if self.portlet else 0
            ),
        }


@view_config(
    route_name='portlet_add',
    renderer='pyramid_bimt:templates/form.pt',
    permission='admin',
    layout='default'
)
class PortletAddForm(PortletEditForm):

    def __call__(self):
        app_assets.need()
        form_assets.need()
        self.request.context = None
        return super(PortletAddForm, self).__call__()


@view_defaults(permission='admin')
class PortletView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context

    @view_config(
        route_name='portlet_list',
        layout='default',
        renderer='pyramid_bimt:templates/portlets.pt',
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        app_assets.need()
        return {
            'portlets': Portlet.query
            .order_by(Portlet.position, Portlet.weight.desc()).all(),
        }
