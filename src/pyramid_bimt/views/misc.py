# -*- coding: utf-8 -*-
"""misc and tool views, etc."""

from datetime import date
from datetime import datetime
from pyramid.httpexceptions import exception_response
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid_bimt.models import User
from pyramid_bimt.static import app_assets
from pyramid_mailer import mailer_factory_from_settings
from pyramid_mailer.message import Message

import os


@view_config(
    route_name='raise_http_error',
    permission='admin',
)
def raise_http_error(request):
    raise exception_response(int(request.matchdict['error_code']))


@view_config(
    route_name='raise_js_error',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/form.pt',
)
def raise_js_error(request):
    app_assets.need()
    return {
        'title': 'JS error',
        'form': """<script type="text/javascript">
      throw new Error('[{now}] Error test.');
    </script>

    <p>[{now}] Error test.</p>""".format(now=datetime.utcnow())
    }


@view_config(
    route_name='config',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/config.pt',
)
def config(request):
    app_assets.need()
    request.layout_manager.layout.hide_sidebar = True
    settings = sorted(request.registry.settings.items(), key=lambda x: x[0])
    environ = sorted(os.environ.items(), key=lambda x: x[0])
    return {
        'title': 'Config',
        'environ': environ,
        'settings': settings
    }


@view_config(
    route_name='bimt_sanity_check',
    layout='default',
    renderer='pyramid_bimt:templates/form.pt',
)
def bimt_sanity_check(request):
    app_assets.need()
    secret = request.registry.settings.get('bimt.app_secret')
    if (('secret' in request.GET and request.GET['secret'] == secret)
            or
            (request.user and 'admins' in [g.name for g in request.user.groups])):  # noqa
        send_sanity_mail(request)
        return {
            'title': 'Sanity check',
            'form': '<p>Sanity check finished and mail sent</p>'
        }
    return {
        'title': 'Not Allowed',
        'form': '<p>Not Allowed</p>'
    }


def send_sanity_mail(request):

    settings = request.registry.settings
    mailer = mailer_factory_from_settings(settings)
    recipient_address = settings.get('mail.info_address')
    errors = []
    for user in User.get_all():
        errors = errors + check_user(user)
    body = render(
        'pyramid_bimt:templates/bimt_sanity_mail.pt',
        {'errors': errors}
    )
    if errors:
        subject = 'Bimt sanity check errors on day: {}'.format(date.today())
    else:
        subject = 'Bimt sanity check is OK!'
    message = Message(
        subject=subject,
        sender=settings['mail.default_sender'],
        recipients=[recipient_address, ],
        body=body,
    )
    mailer.send(message)


def check_user(user):
    errors = []
    if not user.enabled:
        if user.trial:
            errors.append(
                'User {0} is disabled but in trial group!'.format(user.id)
            )
        if user.regular:
            errors.append(
                'User {0} is disabled but in regular group!'.format(user.id)
            )
    if user.enabled and not (user.trial or user.regular):
        errors.append(
            'User {0} is enabled but not trial or regular!'.format(user.id)
        )
    if user.trial and user.regular:
        errors.append(
            'User {0} is both trial and regular!'.format(user.id)
        )
    return errors
