# -*- coding: utf-8 -*-
"""Views for logging in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.models import Group
from pyramid_bimt.models import GroupProperty
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import FormView

import colander
import copy
import deform


@view_defaults(permission=BimtPermissions.manage)
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
        self.request.layout_manager.layout.title = u'Groups'
        return {
            'groups': Group.get_all().all(),
        }


@colander.deferred
def deferred_group_name_validator(node, kw):

    def validator(node, cstruct):
        if Group.by_name(cstruct):
            raise colander.Invalid(
                node, u'Group with name "{}" already exists.'.format(cstruct))

    # skip validation if context already has name set and this name is resent
    if (  # pragma: no branch
        kw.get('request') and kw.get('request').POST and
        isinstance(kw['request'].context, Group) and
        kw['request'].context.name == kw['request'].POST['name']
    ):
        return colander.Length(min=1)

    return validator


@colander.deferred
def deferred_group_product_id_validator(node, kw):

    def validator(node, cstruct):
        if Group.by_product_id(cstruct):
            raise colander.Invalid(
                node,
                u'Group with product id "{}" already exists.'.format(cstruct)
            )

    # skip validation if context already has product_id set and it is resent
    if (  # pragma: no branch
        kw.get('request') and kw.get('request').POST and
        isinstance(kw['request'].context, Group) and
        kw['request'].context.product_id == kw['request'].POST['product_id']
    ):
        return colander.Length(min=1)

    return validator


@view_config(
    route_name='group_add',
    layout='default',
    permission=BimtPermissions.manage,
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
        'properties',
    ]

    def __init__(self, request):
        self.request = request
        self.schema = SQLAlchemySchemaNode(
            Group,
            includes=self.fields,
            overrides={
                'properties': {'includes': ['key', 'value']},
                'name': {'validator': deferred_group_name_validator},
                'product_id': {'validator': deferred_group_product_id_validator}  # noqa
            }
        )

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
            properties=[GroupProperty(key=prop['key'], value=prop['value'])
                        for prop in appstruct.get('properties', [])],
        )

        Session.add(group)
        Session.flush()
        self.request.session.flash(u'Group "{}" added.'.format(group.name))
        return HTTPFound(
            location=self.request.route_path('group_edit', group_id=group.id))

    def appstruct(self):
        appstruct = dict()
        for field in self.fields + ['users', 'properties']:
            if self.request.params.get(field) is not None:
                appstruct[field] = self.request.params[field]

        return appstruct


@view_config(
    route_name='group_edit',
    layout='default',
    permission=BimtPermissions.manage,
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

        # remove properties that are not present in appstruct
        for prop in copy.copy(group.properties):
            if prop.key not in [p['key'] for p in appstruct['properties']]:
                group.properties.remove(prop)

        # update/create properties present in appstruct
        for prop in appstruct['properties']:
            if group.get_property(prop['key'], None) is not None:
                group.set_property(key=prop['key'], value=prop['value'])
            else:
                group.properties.append(
                    GroupProperty(key=prop['key'], value=prop['value']))

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

        if context.properties:
            appstruct['properties'] = [
                {'key': prop.key, 'value': prop.value}
                for prop in context.properties
            ]
        else:
            del appstruct['properties']

        return appstruct
