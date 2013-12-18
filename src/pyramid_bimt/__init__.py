# -*- coding: utf-8 -*-
"""Initializer."""

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_basemodel import Session
from pyramid_bimt.acl import AuditLogFactory
from pyramid_bimt.acl import PortletFactory
from pyramid_bimt.acl import RootFactory
from pyramid_bimt.acl import UserFactory
from pyramid_bimt.acl import groupfinder
from pyramid_bimt.hooks import get_authenticated_user
from sqlalchemy import engine_from_config

import sys


REQUIRED_SETTINGS = [
    'authtkt.secret',
    'bimt.app_name',
    'bimt.app_title',
    'bimt.disabled_user_redirect_path',
    'script_location',
    'session.secret',
    'sqlalchemy.url',
]

REQUIRED_SETTINGS_PRODUCTION = [
    'bimt.jvzoo_regular_period',
    'bimt.jvzoo_secret_key',
    'bimt.jvzoo_trial_period',
    'bimt.piwik_site_id',
    'mail.default_sender',
    'mail.host',
    'mail.password',
    'mail.port',
    'mail.tls',
    'mail.username',
]


def add_routes_auth(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')


def add_routes_user(config):
    config.add_route('users', '/users', factory=UserFactory)
    config.add_route('user_add', '/users/add', factory=UserFactory)
    config.add_route(
        'user', '/users/{user_id}',
        factory=UserFactory, traverse='/{user_id}'
    )
    config.add_route(
        'user_enable', '/users/{user_id}/enable',
        factory=UserFactory, traverse='/{user_id}'
    )
    config.add_route(
        'user_disable', '/users/{user_id}/disable',
        factory=UserFactory, traverse='/{user_id}'
    )
    config.add_route(
        'user_edit', '/users/{user_id}/edit',
        factory=UserFactory, traverse='/{user_id}'
    )


def add_routes_audit_log(config):
    config.add_route('audit_log', '/audit-log', factory=AuditLogFactory)
    config.add_route(
        'audit_log_add',
        '/audit-log/add',
        factory=AuditLogFactory,
    )
    config.add_route(
        'audit_log_delete',
        '/audit-log/{entry_id}/delete',
        factory=AuditLogFactory,
        traverse='/{entry_id}',
    )


def add_routes_portlet(config):
    config.add_route('portlets', '/portlets', factory=PortletFactory)
    config.add_route('portlet_add', '/portlets/add', factory=PortletFactory)
    config.add_route(
        'portlet_edit', '/portlets/{portlet_id}/edit',
        factory=PortletFactory, traverse='/{portlet_id}'
    )


def add_routes_other(config):
    config.add_route('jvzoo', '/jvzoo')
    config.add_route('raise_js_error', '/raise-error/js')
    config.add_route('raise_http_error', '/raise-error/{error_code}')
    config.add_route('config', '/config')


def configure(config, settings={}):

    # Include pyramid layout
    config.include('pyramid_layout')

    # Add route to deform's static resources
    config.add_static_view('deform_static', 'deform:static')

    # Add helpful properties to the request object
    config.set_request_property(
        get_authenticated_user, 'user', reify=True)

    # Setup session factory
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings.get('session.secret', 'secret'))
    config.set_session_factory(session_factory)

    # configure routes
    add_routes_auth(config)
    add_routes_user(config)
    add_routes_audit_log(config)
    add_routes_portlet(config)
    add_routes_other(config)

    # Run a venusian scan to pick up the declarative configuration.
    config.scan('pyramid_bimt', ignore='pyramid_bimt.tests')


def check_required_settings(config):
    # make sure default required settings are set
    for setting in REQUIRED_SETTINGS:
        if setting not in config.registry.settings:
            raise KeyError(
                'The "{}" setting is required, please set '
                'it in your .ini file.'.format(setting))

    # check if we are running with production.ini
    if 'production.ini' in ' '.join(sys.argv).lower():
        # make sure production required settings are set
        for setting in REQUIRED_SETTINGS_PRODUCTION:
            if setting not in config.registry.settings:
                raise KeyError(
                    'The "{}" production setting is required, please set '
                    'it in your production.ini file.'.format(setting))


def includeme(config):
    """Allow developers to use ``config.include('pyramid_bimt')``."""
    check_required_settings(config)

    # Setup the DB session and such
    config.include('pyramid_basemodel')

    # Setup authentication and authorization policies.
    authentication_policy = AuthTktAuthenticationPolicy(
        secret=config.registry.settings.get('authtkt.secret', 'secret'),
        hashalg='sha512',
        callback=groupfinder,
    )
    authorization_policy = ACLAuthorizationPolicy()

    config.set_authorization_policy(authorization_policy)
    config.set_authentication_policy(authentication_policy)

    configure(config, config.registry.settings)


def home(context, request):
    """Default Home view. Should be overwritten by an app."""
    return {
        'title': 'A sample BIMT page',
        'form': None,
    }


def add_home_view(config):
    """Add Home view & route, to serve as example when developing pyramid_bimt
    individually, but not being used in apps."""
    config.add_view(
        'pyramid_bimt.home',
        renderer='pyramid_bimt:templates/form.pt',
        layout='default',
    )


def main(global_config, **settings):
    """This function returns a Pyramid WSGI application and is only used
    when developing BIMT in isolation."""
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)

    config = Configurator(
        settings=settings,
        root_factory=RootFactory,
    )

    includeme(config)
    add_home_view(config)
    return config.make_wsgi_app()
