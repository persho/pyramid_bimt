# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from collections import OrderedDict
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.events import UserCreated
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.models import UserProperty
from pyramid_bimt.security import encrypt
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import DatatablesDataView
from pyramid_bimt.views import FormView
from pyramid_bimt.views import SQLAlchemySchemaNode

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


def validate_email_field(node, kw, field_name):

    email_fields = ['email', 'billing_email']

    def validator(node, cstruct):
        colander.Email()(node, cstruct)
        for email_field in email_fields:
            query = User.query.filter_by(**{email_field: cstruct})
            if query.count() and query.one() != kw['request'].context:
                raise colander.Invalid(
                    node, u'Email {} is already in use.'.format(cstruct))

    # skip validation if context already has email set and this email is resent
    if (  # pragma: no branch
        kw.get('request') and
        isinstance(kw['request'].context, User) and
        getattr(kw['request'].context, field_name) == kw['request'].POST.get(field_name)  # noqa
    ):
        return colander.Email()

    return validator


@colander.deferred
def deferred_user_email_validator(node, kw):
    return validate_email_field(node, kw, 'email')


@colander.deferred
def deferred_user_billing_email_validator(node, kw):
    return validate_email_field(node, kw, 'billing_email')


@view_defaults(permission=BimtPermissions.manage)
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
        xhr=False,
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        self.request.layout_manager.layout.title = u'Users'
        return {'count': User.get_all().count()}

    @view_config(
        route_name='user_view',
        layout='default',
        renderer='pyramid_bimt:templates/user.pt',
    )
    def view(self):
        self.request.layout_manager.layout.title = self.context.email
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
    route_name='user_list',
    permission=BimtPermissions.manage,
    renderer='json',
    xhr=True,
)
class UserListAJAX(DatatablesDataView):
    """Ajax view used to populate AuditLog datatables with JSON data."""
    model = User

    columns = OrderedDict()
    columns['id'] = None
    columns['fullname'] = None
    columns['email'] = None
    columns['groups'] = None
    columns['created'] = None
    columns['modified'] = None
    columns['enable/disable'] = None
    columns['edit'] = None

    def populate_columns(self, user):

        for column in ['id', 'fullname', 'email']:
            if user.enabled:
                self.columns[column] = u'<a href="{}">{}</a>'.format(
                    self.request.route_path('user_view', user_id=user.id),
                    getattr(user, column),
                )
            else:
                self.columns[column] = (
                    u'<a style="text-decoration: '
                    'line-through" href="{}">{}</a>').format(
                    self.request.route_path('user_view', user_id=user.id),
                    getattr(user, column),
                )

        groups = [
            u'<a href="{}">{}</a>'.format(
                self.request.route_path('group_edit', group_id=group.id),
                group.name,
            )
            for group in user.groups
        ]

        self.columns['groups'] = '<span>, </span>'.join(groups)
        self.columns['created'] = user.created.strftime('%Y/%m/%d %H:%M:%S')
        self.columns['modified'] = user.modified.strftime('%Y/%m/%d %H:%M:%S')

        if not user.enabled:
            self.columns['enable/disable'] = """
            <a class="btn btn-xs btn-success" href="{}">
            <span class="glyphicon glyphicon-play"></span> Enable</a>""".format(  # noqa
                self.request.route_path('user_enable', user_id=user.id))
        else:
            self.columns['enable/disable'] = """
            <a class="btn btn-xs btn-danger" href="{}">
            <span class="glyphicon glyphicon-pause"></span> Disable</a>""".format(  # noqa
                self.request.route_path('user_disable', user_id=user.id))

        self.columns['edit'] = """<a class="btn btn-xs btn-primary" href="{}">
            <span class="glyphicon glyphicon-edit"></span> Edit""".format(
            self.request.route_path('user_edit', user_id=user.id))


@view_config(
    route_name='user_add',
    layout='default',
    permission=BimtPermissions.manage,
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
            overrides={
                'properties': {'includes': ['key', 'value']},
                'email': {'validator': deferred_user_email_validator},
                'billing_email': {
                    'validator': deferred_user_billing_email_validator}
            }
        )

        # we don't like the way ColanderAlchemy renders SA Relationships so
        # we manually inject a suitable SchemaNode for groups
        choices = [(group.id, group.name) for group in Group.get_all()]
        enabled = Group.by_name('enabled')
        choices.remove((enabled.id, enabled.name))
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
            properties=[UserProperty(key=prop.get('key'), value=prop.get('value'))  # noqa
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
    permission=BimtPermissions.manage,
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

        groups = [Group.by_id(group_id) for group_id in appstruct['groups']]
        enabled = Group.by_name('enabled')
        if enabled in user.groups:
            groups.append(enabled)
        user.groups = groups

        # remove properties that are not present in appstruct
        for prop in copy.copy(user.properties):
            if prop.key not in [p['key'] for p in appstruct['properties']]:
                user.properties.remove(prop)

        # update/create properties present in appstruct
        for prop in appstruct['properties']:
            if user.get_property(prop['key'], None) is not None:
                user.set_property(key=prop['key'], value=prop.get('value'))
            else:
                user.properties.append(
                    UserProperty(key=prop['key'], value=prop.get('value')))

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
                getattr(context, field, None) and
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

        return appstruct
