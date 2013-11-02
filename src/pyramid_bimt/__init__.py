# -*- coding: utf-8 -*-
"""Initializer."""

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_bimt.acl import UserFactory
from pyramid_bimt.acl import groupfinder
from pyramid_bimt.hooks import get_authenticated_user


def includeme(config):
    """Allow developers to use ``config.include('pyramid_bimt')``."""

    # Setup the DB session and such
    config.include('pyramid_basemodel')

    # Add helpful properties to the request object
    settings = config.registry.settings
    config.set_request_property(
        get_authenticated_user, 'user', reify=True)

    # Setup authentication and authorization policies.
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings.get('session.secret', 'secret'))
    authentication_policy = AuthTktAuthenticationPolicy(
        secret=settings.get('authtkt.secret', 'secret'),
        hashalg='sha512',
        callback=groupfinder,
    )
    authorization_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)
    config.set_session_factory(session_factory)

    # configure routes
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('audit-log', '/audit-log')
    config.add_route('users', '/users', factory=UserFactory)
    config.add_route(
        'user', '/users/{user_id}', factory=UserFactory, traverse='/{user_id}')
    config.add_route(
        'user_enable',
        '/users/{user_id}/enable',
        factory=UserFactory,
        traverse='/{user_id}',
    )
    config.add_route(
        'user_disable',
        '/users/{user_id}/disable',
        factory=UserFactory,
        traverse='/{user_id}',
    )

    # Run a venusian scan to pick up the declarative configuration.
    config.scan('pyramid_bimt', ignore='pyramid_simpleauth.tests')
