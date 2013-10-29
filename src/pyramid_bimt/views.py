# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import view_config
from pyramid_bimt.models import User
from pyramid_bimt.security import verify
from pyramid_deform import FormView

import deform
import colander


class LoginSchema(colander.MappingSchema):
    email = colander.SchemaNode(
        colander.String(),
        title='Email',
    )
    password = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget(size=128),
        title='Password',
    )


@view_config(
    route_name='login',
    renderer='templates/form.pt',
    layout='default',
)
class LoginForm(FormView):
    schema = LoginSchema()
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
            self.request.session.flash(u"Login successful.")
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
