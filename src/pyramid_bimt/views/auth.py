# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import view_config
from pyramid_bimt.events import UserLoggedIn
from pyramid_bimt.events import UserLoggedOut
from pyramid_bimt.events import UserChangedPassword
from pyramid_bimt.models import User
from pyramid_bimt.security import encrypt
from pyramid_bimt.security import generate
from pyramid_bimt.security import verify
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView


@view_config(
    route_name='login',
    permission=NO_PERMISSION_REQUIRED,
    layout='default',
    renderer='pyramid_bimt:templates/form.pt',
)
class LoginForm(FormView):
    schema = SQLAlchemySchemaNode(User, includes=['email', 'password'])
    buttons = ('login', 'reset password')
    title = 'Login'
    form_options = (('formid', 'login'), ('method', 'POST'))

    def __call__(self):
        app_assets.need()
        form_assets.need()
        self.request.layout_manager.layout.hide_sidebar = True
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
        if (
            password is not None and
            user is not None and
            verify(password, user.password)
        ):
            headers = remember(self.request, user.email)
            self.request.registry.notify(UserLoggedIn(self.request, user))
            self.request.session.flash(u'Login successful.')

            if not user.enabled:
                self.request.session.flash(
                    u'Your account is disabled.', 'warning')
                return HTTPFound(
                    location=self.request.registry.settings['bimt.disabled_user_redirect_path'],  # noqa
                    headers=headers
                )

            return HTTPFound(location=came_from, headers=headers)
        self.request.session.flash(u'Login failed.', 'error')

    def reset_password_success(self, appstruct):
        came_from = self.request.params.get(
            'came_from', self.request.application_url)
        email = appstruct['email'].lower()
        user = User.by_email(email)
        if user is not None:

            # change user's password and fire event
            password = generate()
            user.password = encrypt(password)
            self.request.registry.notify(
                UserChangedPassword(self.request, user, password)
            )

            self.request.session.flash(
                u'A new password was sent to your email.')
            return HTTPFound(location=came_from)
        self.request.session.flash(
            u'Password reset failed. Make sure you '
            'have correctly entered your email address.', 'error')

    def appstruct(self):
        return {
            'email': self.request.params.get('email', ''),
            'password': self.request.params.get('password', ''),
        }


@view_config(route_name='logout', permission=NO_PERMISSION_REQUIRED)
def logout(context, request):
    """Logout view.  Always redirects the user to where he came from.

    :result: Redirect to came_from.
    :rtype: pyramid.httpexceptions.HTTPFound
    """
    request.registry.notify(UserLoggedOut(request, request.user))
    headers = forget(request)
    request.session.flash(u'You have been logged out.')
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)


@view_config(
    context=HTTPForbidden,
    permission=NO_PERMISSION_REQUIRED,
    accept='text/html'
)
def forbidden_redirect(context, request):
    """Redirect to the login form for anonymous users.

    :result: Redirect to the login form.
    :rtype: pyramid.httpexceptions.HTTPFound
    """
    request.session.flash(u'Insufficient privileges.')
    location = request.route_path('login', _query={'came_from': request.url})
    return HTTPFound(location=location)
