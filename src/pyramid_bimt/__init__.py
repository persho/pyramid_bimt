# -*- coding: utf-8 -*-

from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from pyramid_bimt.hooks import get_authenticated_user, get_is_authenticated
# from .hooks import get_roles, get_user_json
# from .hooks import get_is_post_login, get_is_post_signup
# from .tree import AuthRoot


def includeme(config):
    """Allow developers to use ``config.include('pyramid_simpleauth')``.

    """

    # Add helpful properties to the request object
    settings = config.registry.settings
    config.set_request_property(
        get_is_authenticated, 'is_authenticated', reify=True)
    config.set_request_property(
        get_authenticated_user, 'user', reify=True)

    # Setup authentication and authorization policies.
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings.get('session.secret', 'secret'))
    authentication_policy = AuthTktAuthenticationPolicy(
        secret=settings.get('authtkt.secret', 'secret'), hashalg='sha512')
    authorization_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)
    config.set_session_factory(session_factory)

    # Run a venusian scan to pick up the declarative configuration.
    config.scan('pyramid_bimt', ignore='pyramid_simpleauth.tests')
