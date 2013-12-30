# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_bimt.static import table_assets
from pyramid_deform import FormView

import colander
import deform


@view_defaults(route_name='user', permission='admin')
class UserView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context

    @view_config(
        route_name='users',
        renderer='pyramid_bimt:templates/users.pt',
        layout='default',
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        app_assets.need()
        table_assets.need()
        return {
            'users': User.get_all(),
        }

    @view_config(
        renderer='pyramid_bimt:templates/user.pt',
        layout='default',
    )
    def view(self):
        app_assets.need()
        user_ = self.context
        properties = (self.view.schema.dictify(user_) or {}).get('properties', [])  # noqa
        return {
            'user': user_,
            'audit_log_entries': AuditLogEntry.get_all(
                filter_by={'user_id': user_.id}),
            'properties': properties,
        }

    @view_config(route_name='user_enable')
    def user_enable(self):
        user = self.context
        if user.enable():
            self.request.registry.notify(UserEnabled(self.request, user))
            self.request.session.flash('User {} enabled.'.format(user.email))
        else:
            self.request.session.flash(
                'User {} already enabled, skipping.'.format(user.email))
        return HTTPFound(
            location=self.request.route_path('users')
        )

    @view_config(route_name='user_disable')
    def user_disable(self):
        user = self.context
        if user.disable():
            self.request.registry.notify(UserDisabled(self.request, user))
            self.request.session.flash('User {} disabled.'.format(user.email))
        else:
            self.request.session.flash(
                'User {} already disabled, skipping.'.format(user.email))
        return HTTPFound(
            location=self.request.route_path('users')
        )

    view.schema = SQLAlchemySchemaNode(
        User,
        includes=['properties'],
        overrides={'properties': {'includes': ['key', 'value']}}
    )


def group_validator(form, value):
    if Group.by_name(value) is None:
        raise colander.Invalid(form, 'Group must be one of: {}'.format(
            ', '.join([g.name for g in Group.query.all()])))


class UserEditSchema(colander.MappingSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.Email(),
    )
    fullname = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget()
    )
    groups = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(),
            name='Group',
            validator=group_validator
        ),
    )


@view_config(
    route_name='user_edit',
    renderer='pyramid_bimt:templates/form.pt',
    permission='admin',
    layout='default',
)
class UserEditForm(FormView):
    TITLE_EDIT = 'Edit User'
    TITLE_ADD = 'Add User'

    buttons = ('save', )
    title = TITLE_EDIT
    form_options = (('formid', 'useredit'), ('method', 'POST'))
    schema = UserEditSchema()

    def __call__(self):
        app_assets.need()
        form_assets.need()

        self.edited_user = self.request.context
        if not self.edited_user:
            self.title = self.TITLE_ADD

        self.request.layout_manager.layout.current_page = self.title

        result = super(UserEditForm, self).__call__()
        if isinstance(result, dict):
            result['title'] = self.title
        return result

    def save_success(self, appstruct):
        if self.edited_user:
            # edit user
            user = self.edited_user
            user.email = appstruct['email'].lower()
            user.fullname = appstruct['fullname']
            user.groups = [Group.by_name(name) for name in appstruct['groups']]
            self.request.session.flash(
                u'User {} has been modified.'.format(user.email))
        else:
            # add user
            user = User(
                email=appstruct['email'].lower(),
                fullname=appstruct['fullname'],
                groups=[Group.by_name(name) for name in appstruct['groups']]
            )
            Session.add(user)
            self.request.session.flash(
                u'User {} has been added.'.format(user.email))

        Session.flush()  # this is needed, so that we get user.id NOW
        return HTTPFound(
            location=self.request.route_path('user', user_id=user.id))

    def appstruct(self):
        params_groups = self.request.params.get('groups')
        if self.edited_user and params_groups is None:
            groups = [g.name for g in self.edited_user.groups]
        else:
            groups = [g for g in params_groups or []]

        return {
            'email': self.request.params.get(
                'email', self.edited_user.email if self.edited_user else u''
            ),
            'fullname': self.request.params.get(
                'fullname',
                self.edited_user.fullname if self.edited_user else u''
            ),
            'groups': groups
        }


@view_config(
    route_name='user_add',
    renderer='pyramid_bimt:templates/form.pt',
    permission='admin',
    layout='default'
)
class UserAddForm(UserEditForm):

    def __call__(self):
        app_assets.need()
        form_assets.need()
        self.request.context = None
        return super(UserAddForm, self).__call__()
