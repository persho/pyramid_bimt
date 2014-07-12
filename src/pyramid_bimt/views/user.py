# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.events import UserCreated
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from pyramid_bimt.security import encrypt
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import FormView

import colander
import copy
import deform


@colander.deferred
def deferred_groups_validator(node, kw):
    request = kw['request']

    def validator(node, cstruct):
        id_ = str(Group.by_name('admins').id)
        if (not request.user.admin) and (id_ in cstruct):
            raise colander.Invalid(
                node, u'Only admins can add users to "admins" group.')
    return validator


@view_defaults(permission='manage_users')
class UserView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        app_assets.need()
        table_assets.need()

    @view_config(
        route_name='user_list',
        layout='default',
        renderer='pyramid_bimt:templates/users.pt',
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        return {
            'users': User.get_all(),
        }

    @view_config(
        route_name='user_view',
        layout='default',
        renderer='pyramid_bimt:templates/user.pt',
    )
    def view(self):
        return {
            'user': self.context,
            'audit_log_entries': self.context.audit_log_entries,
            'properties': self.context.properties,
        }

    @view_config(route_name='user_enable')
    def enable(self):
        user = self.context
        if user.enable():
            self.request.registry.notify(UserEnabled(self.request, user))
            self.request.session.flash('User "{}" enabled.'.format(user.email))
        else:
            self.request.session.flash(
                'User "{}" already enabled, skipping.'.format(user.email))
        return HTTPFound(
            location=self.request.route_path('user_list')
        )

    @view_config(route_name='user_disable')
    def disable(self):
        user = self.context
        if user.disable():
            self.request.registry.notify(UserDisabled(self.request, user))
            self.request.session.flash(
                'User "{}" disabled.'.format(user.email))
        else:
            self.request.session.flash(
                'User "{}" already disabled, skipping.'.format(user.email))
        return HTTPFound(
            location=self.request.route_path('user_list')
        )

    @view_config(route_name='user_unsubscribe', permission='user')
    def unsubscribe(self):
        request = self.context.request

        if request.user.unsubscribe():
            request.session.flash(
                u'You have been unsubscribed from newsletter.')
        else:
            request.session.flash(
                u'You are already unsubscribed from newsletter.')

        return HTTPFound(location='/')


@view_config(
    route_name='user_add',
    layout='default',
    permission='manage_users',
    renderer='pyramid_bimt:templates/form.pt',
)
class UserAdd(FormView):
    buttons = ('submit', )
    title = 'Add User'
    form_options = (('formid', 'user-add'), ('method', 'POST'))
    fields = [
        'email',
        'password',
        'fullname',
        'affiliate',
        'billing_email',
        'valid_to',
        'last_payment',
        'properties',
    ]

    def __init__(self, request):
        self.request = request
        self.schema = SQLAlchemySchemaNode(
            User,
            includes=self.fields,
            overrides={'properties': {'includes': ['key', 'value']}}
        )

        # we don't like the way ColanderAlchemy renders SA Relationships so
        # we manually inject a suitable SchemaNode for groups
        choices = [(group.id, group.name) for group in Group.get_all()]
        if not request.user.admin:
            admins = Group.by_name('admins')
            choices.remove((admins.id, admins.name))
        self.schema.add(
            node=colander.SchemaNode(
                colander.Set(),
                name='groups',
                missing=[],
                widget=deform.widget.CheckboxChoiceWidget(values=choices),
                validator=deferred_groups_validator,
            ),
        )

    def submit_success(self, appstruct):
        user = User(
            email=appstruct.get('email'),
            fullname=appstruct.get('fullname'),
            affiliate=appstruct.get('affiliate'),
            billing_email=appstruct.get('billing_email'),
            valid_to=appstruct.get('valid_to'),
            last_payment=appstruct.get('last_payment'),
            groups=[Group.by_id(group_id) for group_id in appstruct.get('groups', [])],  # noqa
            properties=[UserProperty(key=prop['key'], value=prop['value'])
                        for prop in appstruct.get('properties', [])],
        )

        if appstruct.get('password'):  # pragma: no branch
            user.password = encrypt(appstruct['password'])

        Session.add(user)
        Session.flush()
        self.request.registry.notify(
            UserCreated(
                self.request,
                user,
                appstruct.get('password'),
                u'Created manually by {}'.format(self.request.user.email)
            )
        )
        self.request.session.flash(u'User "{}" added.'.format(user.email))
        return HTTPFound(
            location=self.request.route_path('user_view', user_id=user.id))

    def appstruct(self):
        appstruct = dict()
        for field in self.fields + ['groups', 'properties']:
            if self.request.params.get(field) is not None:
                appstruct[field] = self.request.params[field]

        return appstruct


@view_config(
    route_name='user_edit',
    layout='default',
    permission='manage_users',
    renderer='pyramid_bimt:templates/form.pt',
)
class UserEdit(UserAdd):
    buttons = ('save', )
    title = 'Edit User'
    form_options = (('formid', 'user-edit'), ('method', 'POST'))

    def save_success(self, appstruct):
        user = self.request.context

        user.email = appstruct.get('email')
        user.fullname = appstruct.get('fullname')
        user.affiliate = appstruct.get('affiliate')
        user.billing_email = appstruct.get('billing_email')
        user.valid_to = appstruct.get('valid_to')
        user.last_payment = appstruct.get('last_payment')

        if appstruct.get('password'):
            user.password = encrypt(appstruct['password'])

        user.groups = [
            Group.by_id(group_id) for group_id in appstruct['groups']
        ]

        # remove properties that are not present in appstruct
        for prop in copy.copy(user.properties):
            if prop.key not in [p['key'] for p in appstruct['properties']]:
                user.properties.remove(prop)

        # update/create properties present in appstruct
        for prop in appstruct['properties']:
            if user.get_property(prop['key'], None) is not None:
                user.set_property(key=prop['key'], value=prop['value'])
            else:
                user.properties.append(
                    UserProperty(key=prop['key'], value=prop['value']))

        self.request.session.flash(
            u'User "{}" modified.'.format(user.email))
        return HTTPFound(
            location=self.request.route_path(
                'user_view', user_id=user.id))

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

        if context.properties:
            appstruct['properties'] = [
                {'key': prop.key, 'value': prop.value}
                for prop in context.properties
            ]
        else:
            del appstruct['properties']

        return appstruct
