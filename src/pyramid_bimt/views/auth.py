# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import view_config
from pyramid_bimt.events import UserLoggedIn
from pyramid_bimt.events import UserLoggedOut
from pyramid_bimt.models import User
from pyramid_bimt.security import encrypt
from pyramid_bimt.security import generate
from pyramid_bimt.security import verify
from pyramid_deform import FormView
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

PASSWORD_RESET_EMAIL_BODY = """
Hi {fullname},

your new password for {app_title} is: {password}

Login to the members' area:
{login_url}

Regards,
The Big IM Toolbox Team
"""


@view_config(
    route_name='login',
    renderer='pyramid_bimt:templates/form.pt',
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
        user = User.by_email(email)
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
        user = User.by_email(email)
        if user is not None:

            # change user's password and send email
            password = generate()
            user.password = encrypt(password)
            mailer = get_mailer(self.request)
            message = Message(
                subject="{} Password Reset".format(
                    self.request.registry.settings['bimt.app_title']),
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
