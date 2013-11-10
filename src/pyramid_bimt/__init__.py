# -*- coding: utf-8 -*-
"""Initializer."""

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_basemodel import Session
from pyramid_bimt.acl import AuditLogFactory
from pyramid_bimt.acl import RootFactory
from pyramid_bimt.acl import UserFactory
from pyramid_bimt.acl import groupfinder
from pyramid_bimt.hooks import get_authenticated_user
from sqlalchemy import engine_from_config


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
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('audit-log', '/audit-log')
    config.add_route('users', '/users', factory=UserFactory)
    config.add_route('user', '/users/*traverse', factory=UserFactory)

    config.add_route('audit_log', '/audit_log', factory=AuditLogFactory)
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

    # Run a venusian scan to pick up the declarative configuration.
    config.scan('pyramid_bimt', ignore='pyramid_bimt.tests')


def includeme(config):
    """Allow developers to use ``config.include('pyramid_bimt')``."""

    # Get settings
    settings = config.registry.settings

    # Setup the DB session and such
    config.include('pyramid_basemodel')

    # Setup authentication and authorization policies.
    authentication_policy = AuthTktAuthenticationPolicy(
        secret=settings.get('authtkt.secret', 'secret'),
        hashalg='sha512',
        callback=groupfinder,
    )
    authorization_policy = ACLAuthorizationPolicy()

    config.set_authorization_policy(authorization_policy)
    config.set_authentication_policy(authentication_policy)

    configure(config, settings)


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
