# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import view_config
from pyramid_basemodel import Session
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.events import UserLoggedIn
from pyramid_bimt.events import UserLoggedOut
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import AuditLogEventType
from pyramid_bimt.models import User
from pyramid_bimt.security import verify
from pyramid_deform import FormView
from colanderalchemy import SQLAlchemySchemaNode

import deform
import colander


@view_config(
    route_name='login',
    renderer='templates/form.pt',
    layout='default',
)
class LoginForm(FormView):
    schema = SQLAlchemySchemaNode(User, includes=["username", "password"])
    buttons = ('login', )
    title = 'Login'
    form_options = (('formid', 'login'), ('method', 'POST'))

    def __call__(self):
        result = super(LoginForm, self).__call__()
        if isinstance(result, dict):
            result['title'] = self.title
        return result

    def login_success(self, appstruct):
        came_from = self.request.params.get(
            'came_from', self.request.application_url)
        email = appstruct['email'].lower()
        password = appstruct['password'].lower()
        user = User.get(email)
        if (user is not None and verify(password, user.password)):
            headers = remember(self.request, user.email)
            self.request.registry.notify(UserLoggedIn(self.request, user))
            self.request.session.flash(u"Login successful.")

            if not user.enabled:
                self.request.session.flash(
                    u"Your account is disabled.", 'warning')

            return HTTPFound(location=came_from, headers=headers)
        self.request.session.flash(u"Login failed.", 'error')

    def appstruct(self):
        return {
            'email': self.request.params.get('email', ''),
            'password': self.request.params.get('password', ''),
        }


@view_config(route_name='logout')
def logout(context, request):
    """Logout view.  Always redirects the user to where he came from.

    :result: Redirect to came_from.
    :rtype: pyramid.httpexceptions.HTTPFound
    """
    request.registry.notify(UserLoggedOut(request, request.user))
    headers = forget(request)
    request.session.flash(u"You have been logged out.")
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)


@view_config(context=HTTPForbidden, accept='text/html')
def forbidden_redirect(context, request):
    """Redirect to the login form for anonymous users.

    :result: Redirect to the login form.
    :rtype: pyramid.httpexceptions.HTTPFound
    """
    location = request.route_url('login', _query={'came_from': request.url})
    return HTTPFound(location=location)


@view_config(
    route_name='users',
    permission='admin',
    renderer='templates/users.pt',
    layout='default',
)
def users(request):
    return {
        'users': User.get_all(),
    }


@view_config(
    route_name='user',
    permission='admin',
    renderer='templates/user.pt',
    layout='default',
)
def user(request):
    user_ = request.context
    fields = []
    skip = ['profile', 'get', 'get_all', 'get_by_id', 'password', 'user']

    for attr in [attr for attr in user_.__class__.__dict__ if not attr.startswith('_')]:  # noqa
        if attr in skip:
            continue
        elif attr == 'groups':
            fields.append(
                {'key': 'user_{}'.format(attr), 'value': ', '.join([g.name for g in user_.groups])})  # noqa
        else:
            fields.append(
                {'key': 'user_{}'.format(attr), 'value': getattr(user_, attr)})

    for attr in [attr for attr in user_.profile.__class__.__dict__ if not attr.startswith('_')]:  # noqa
        if attr in skip:
            continue
        fields.append(
            {'key': 'profile_{}'.format(attr), 'value': getattr(user_.profile, attr)})  # noqa

    return {
        'user': user_,
        'fields': fields,
    }


@view_config(route_name='user_enable', permission='admin')
def user_enable(request):
    user = request.context
    if user.enable():
        request.registry.notify(UserEnabled(request, user))
        request.session.flash('User {} enabled.'.format(user.email))
    else:
        request.session.flash(
            'User {} already enabled, skipping.'.format(user.email))
    return HTTPFound(location=request.route_path('user', user_id=user.email))


@view_config(route_name='user_disable', permission='admin')
def user_disable(request):
    user = request.context
    if user.disable():
        request.registry.notify(UserDisabled(request, user))
        request.session.flash('User {} disabled.'.format(user.email))
    else:
        request.session.flash(
            'User {} already disabled, skipping.'.format(user.email))
    return HTTPFound(location=request.route_path('user', user_id=user.email))


@view_config(
    route_name='audit_log',
    permission='admin',
    renderer='templates/audit_log.pt',
    layout='default',
)
def audit_log(request):
    return {
        'entries': AuditLogEntry.get_all(),
    }


@view_config(
    route_name='audit_log_delete',
    permission='admin',
)
def audit_log_delete(request):
    entry = request.context
    Session.delete(entry)
    request.session.flash(u'Audit log entry deleted.')
    return HTTPFound(location=request.route_path('audit_log'))


def users_ids():
    users = User.get_all()
    return [(user.id, user.email) for user in users]


def event_types_ids():
    types = AuditLogEventType.get_all()
    return [(type_.id, type_.name) for type_ in types]


class AuditLogAddEntrySchema(colander.Schema):
    timestamp = colander.SchemaNode(
        colander.DateTime(),
        title='Timestamp',
    )
    user_id = colander.SchemaNode(
        colander.Integer(),
        title='User ID',
        widget=deform.widget.SelectWidget(values=users_ids())
    )
    event_type_id = colander.SchemaNode(
        colander.Integer(),
        title='Event Type ID',
        widget=deform.widget.SelectWidget(values=event_types_ids())
    )
    comment = colander.SchemaNode(
        colander.String(),
        title='Comment',
        missing=u'Manual audit log entry',
    )


@view_config(
    route_name='audit_log_add',
    renderer='templates/form.pt',
    layout='default',
    permission='admin',
)
class AuditLogAddEntryForm(FormView):
    schema = AuditLogAddEntrySchema()
    buttons = ('submit', )
    title = 'Add Audit log entry'
    form_options = (('formid', 'login'), ('method', 'POST'))

    def __call__(self):
        result = super(AuditLogAddEntryForm, self).__call__()
        if isinstance(result, dict):
            result['title'] = self.title
        return result

    def submit_success(self, appstruct):
        entry = AuditLogEntry(
            timestamp=appstruct['timestamp'],
            user_id=appstruct['user_id'],
            event_type_id=appstruct['event_type_id'],
            comment=appstruct['comment'],
        )
        Session.add(entry)
        self.request.session.flash(u"Audit log entry added.")
        return HTTPFound(location=self.request.route_path('audit_log'))

    def appstruct(self):
        return {
            'timestamp': self.request.params.get('timestamp', None),
            'user_id': self.request.params.get('user_id', 0),
            'event_type_id': self.request.params.get('event_type_id', 0),
            'comment': self.request.params.get('comment', ''),
        }
