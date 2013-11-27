# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Session
from pyramid_bimt.events import UserDisabled
from pyramid_bimt.events import UserEnabled
from pyramid_bimt.events import UserLoggedIn
from pyramid_bimt.events import UserLoggedOut
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.models import Group
from pyramid_bimt.models import User
from pyramid_bimt.security import encrypt
from pyramid_bimt.security import generate
from pyramid_bimt.security import verify
from pyramid_deform import FormView
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from sqlalchemy.orm.exc import NoResultFound

import colander
import deform

PASSWORD_RESET_EMAIL_BODY = """
Hi {fullname},

your new password for {app_title} is: {password}

Login at {login_url}.


Regards,
The Big IM Toolbox Team
"""


@view_config(
    route_name='login',
    renderer='templates/form.pt',
    layout='default',
)
class LoginForm(FormView):
    schema = SQLAlchemySchemaNode(User, includes=["email", "password"])
    buttons = ('login', 'reset password')
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
        password = appstruct['password']
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

    def reset_password_success(self, appstruct):
        came_from = self.request.params.get(
            'came_from', self.request.application_url)
        email = appstruct['email'].lower()
        user = User.get(email)
        if user is not None:

            # change user's password and send email
            password = generate()
            user.password = encrypt(password)
            mailer = get_mailer(self.request)
            message = Message(
                subject="{} Password Reset".format(
                    self.request.registry.settings['bimt.app_name']),
                sender=self.request.registry.settings['mail.default_sender'],
                recipients=[user.email, ],
                body=PASSWORD_RESET_EMAIL_BODY.format(
                    fullname=user.fullname,
                    password=password,
                    login_url=self.request.route_url('login'),
                    app_title=self.request.registry.settings['bimt.app_title']
                ),
            )
            mailer.send(message)

            self.request.session.flash(
                u"A new password was sent to your email.")
            return HTTPFound(location=came_from)
        self.request.session.flash(
            u"Password reset failed. Make sure you "
            "have correctly entered your email address.", 'error')

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


@view_defaults(route_name='user', permission='admin')
class UserView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context

    @view_config(
        route_name='users',
        renderer='templates/users.pt',
        layout='default',
    )
    def list(self):
        return {
            'users': User.get_all(),
        }

    @view_config(
        renderer='templates/user.pt',
        layout='default',
    )
    def view(self):
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
        includes=["properties"],
        overrides={"properties": {"includes": ["key", "value"]}}
    )


def group_validator(form, value):
    try:
        Group.get(value)
    except NoResultFound:
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
            name="Group",
            validator=group_validator
        ),
    )


@view_config(
    route_name='user_edit',
    renderer='templates/form.pt',
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
        self.edited_user = self.request.context
        if not self.edited_user:
            self.title = self.TITLE_ADD

        self.request.layout_manager.layout.app_name = \
            self.request.registry.settings['bimt.app_name']
        self.request.layout_manager.layout.current_page = self.title

        result = super(UserEditForm, self).__call__()
        if isinstance(result, dict):
            result['title'] = self.title
        return result

    def save_success(self, appstruct):
        if self.edited_user:
            # edit user
            user = self.edited_user
            user.email = appstruct['email']
            user.fullname = appstruct['fullname']
            user.groups = [Group.get(name) for name in appstruct['groups']]
            self.request.session.flash(
                u"User {} has been changed.".format(user.email))
        else:
            # add user
            user = User(
                email=appstruct['email'],
                fullname=appstruct['fullname'],
                groups=[Group.get(name) for name in appstruct['groups']]
            )
            Session.add(user)
            self.request.session.flash(
                u"User {} has been added.".format(user.email))

        return HTTPFound(location=self.request.route_url('users'))

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
    renderer='templates/form.pt',
    permission='admin',
    layout='default'
)
class UserAddForm(UserEditForm):

    def __call__(self):
        self.request.context = None
        return super(UserAddForm, self).__call__()


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


@view_config(
    route_name='audit_log_add',
    renderer='templates/form.pt',
    layout='default',
    permission='admin',
)
class AuditLogAddEntryForm(FormView):
    schema = SQLAlchemySchemaNode(
        AuditLogEntry,
        includes=['timestamp', 'user_id', 'event_type_id', 'comment']
    )
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
