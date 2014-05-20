# -*- coding: utf-8 -*-
"""Views for logging in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import FormView

import colander
import deform


@view_defaults(permission='admin')
class GroupView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        app_assets.need()
        table_assets.need()

    @view_config(
        route_name='group_list',
        layout='default',
        renderer='pyramid_bimt:templates/groups.pt',
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        return {
            'groups': Group.get_all().all(),
        }


@view_config(
    route_name='group_add',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class GroupAdd(FormView):
    buttons = ('submit', )
    title = 'Add Group'
    form_options = (('formid', 'group-add'), ('method', 'POST'))
    fields = [
        'name',
        'product_id',
        'validity',
        'trial_validity',
        'forward_ipn_to_url',
    ]

    def __init__(self, request):
        self.request = request
        self.schema = SQLAlchemySchemaNode(Group, includes=self.fields)

        # we don't like the way ColanderAlchemy renders SA Relationships so
        # we manually inject a suitable SchemaNode for users
        choices = [(user.id, user.email) for user in User.get_all()]
        self.schema.add(
            node=colander.SchemaNode(
                colander.Set(),
                name='users',
                missing=[],
                widget=deform.widget.CheckboxChoiceWidget(
                    values=choices, inline=True),
            ),
        )

    def submit_success(self, appstruct):
        group = Group(
            name=appstruct.get('name'),
            product_id=appstruct.get('product_id'),
            validity=appstruct.get('validity'),
            trial_validity=appstruct.get('trial_validity'),
            forward_ipn_to_url=appstruct.get('forward_ipn_to_url'),
            users=[User.by_id(user_id) for user_id in appstruct.get('users', [])],  # noqa
        )

        Session.add(group)
        Session.flush()
        self.request.session.flash(u'Group "{}" added.'.format(group.name))
        return HTTPFound(
            location=self.request.route_path('group_edit', group_id=group.id))

    def appstruct(self):
        appstruct = dict()
        for field in self.fields + ['users', ]:
            if self.request.params.get(field) is not None:
                appstruct[field] = self.request.params[field]

        return appstruct


@view_config(
    route_name='group_edit',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class GroupEdit(GroupAdd):
    buttons = ('save', )
    title = 'Edit Group'
    form_options = (('formid', 'group-edit'), ('method', 'POST'))

    def save_success(self, appstruct):
        group = self.request.context

        group.name = appstruct.get('name')
        group.product_id = appstruct.get('product_id')
        group.validity = appstruct.get('validity')
        group.trial_validity = appstruct.get('trial_validity')
        group.forward_ipn_to_url = appstruct.get('forward_ipn_to_url')

        group.users = [User.by_id(user_id) for user_id in appstruct.get('users', [])]  # noqa

        self.request.session.flash(u'Group "{}" modified.'.format(group.name))
        return HTTPFound(
            location=self.request.route_path('group_edit', group_id=group.id))

    def appstruct(self):
        context = self.request.context
        appstruct = dict()
        for field in self.fields:
            if (
                hasattr(context, field) and
                getattr(context, field) is not None
            ):
                appstruct[field] = getattr(context, field)

        if context.users:
            appstruct['users'] = [str(u.id) for u in context.users]
        return appstruct
