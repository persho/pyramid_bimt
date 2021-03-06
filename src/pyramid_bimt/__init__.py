# -*- coding: utf-8 -*-
"""Initializer."""

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.settings import asbool
from pyramid_basemodel import Session
from pyramid_beaker import session_factory_from_settings
from pyramid_bimt import sanitycheck
from pyramid_bimt.acl import AuditLogFactory
from pyramid_bimt.acl import BimtPermissions
from pyramid_bimt.acl import GroupFactory
from pyramid_bimt.acl import MailingFactory
from pyramid_bimt.acl import PortletFactory
from pyramid_bimt.acl import RootFactory
from pyramid_bimt.acl import UserFactory
from pyramid_bimt.acl import groupfinder
from pyramid_bimt.const import Modes
from pyramid_bimt.hooks import get_authenticated_user
from sqlalchemy import engine_from_config

import deform
import logging
import pkg_resources
import requests
import sys
import urllib

logger = logging.getLogger('init')


REQUIRED_SETTINGS = [
    'authtkt.secret',  # used for auth_tkt cookie signing
    'bimt.app_name',
    'bimt.app_title',
    'bimt.disabled_user_redirect_path',
    'bimt.encryption_aes_16b_key',
    'bimt.referral_url',
    'bimt.affiliate_text',
    'script_location',
    'session.encrypt_key',  # a fairly long randomly generated string
    'session.key',  # name of the cookie key used to save the session under
    'session.secret',  # used with the HMAC to ensure session integrity
    'session.type',  # usually 'cookie'
    'session.validate_key',  # used to sign the AES encrypted data
    'sqlalchemy.url',
]

REQUIRED_SETTINGS_PRODUCTION = [
    'bimt.jvzoo_secret_key',
    'bimt.clickbank_secret_key',
    'bimt.piwik_site_id',
    'bimt.amqp_username',
    'bimt.amqp_password',
    'bimt.amqp_apiurl',
    'bimt.kill_cloudamqp_connections',
    'bimt.products_to_ignore',
    'bimt.referrals_mail_username',
    'bimt.referrals_mail_password',
    'bimt.referrals_mail_sender',
    'mail.default_sender',
    'mail.host',
    'mail.password',
    'mail.port',
    'mail.tls',
    'mail.username',
]


def add_routes_auth(config):
    config.add_route('login', '/login/')
    config.add_route('logout', '/logout/')


def add_routes_user(config):
    config.add_route('user_list', '/users/', factory=UserFactory)
    config.add_route('user_add', '/user/add/', factory=UserFactory)
    config.add_route(
        'user_view', '/user/{user_id}/',
        factory=UserFactory, traverse='/{user_id}/'
    )
    config.add_route(
        'user_enable', '/user/{user_id}/enable/',
        factory=UserFactory, traverse='/{user_id}'
    )
    config.add_route(
        'user_disable', '/user/{user_id}/disable/',
        factory=UserFactory, traverse='/{user_id}'
    )
    config.add_route(
        'user_edit', '/user/{user_id}/edit/',
        factory=UserFactory, traverse='/{user_id}'
    )
    config.add_route(
        'user_unsubscribe', '/unsubscribe/', factory=UserFactory
    )


def add_routes_group(config):
    config.add_route('group_list', '/groups/', factory=GroupFactory)
    config.add_route('group_add', '/group/add/', factory=GroupFactory)
    config.add_route(
        'group_edit', '/group/{group_id}/edit/',
        factory=GroupFactory, traverse='/{group_id}'
    )


def add_routes_audit_log(config):
    config.add_route('audit_log', '/activity/', factory=AuditLogFactory)
    config.add_route(
        'audit_log_add',
        '/audit-log/add/',
        factory=AuditLogFactory,
    )
    config.add_route(
        'audit_log_delete',
        '/audit-log/{entry_id}/delete/',
        factory=AuditLogFactory,
        traverse='/{entry_id}',
    )
    config.add_route(
        'audit_log_read_all', '/audit_log_read_all/', factory=AuditLogFactory)


def add_routes_portlet(config):
    config.add_route('portlet_list', '/portlets/', factory=PortletFactory)
    config.add_route('portlet_add', '/portlet/add/', factory=PortletFactory)
    config.add_route(
        'portlet_edit', '/portlet/{portlet_id}/edit/',
        factory=PortletFactory, traverse='/{portlet_id}'
    )


def add_routes_mailing(config):
    config.add_route('mailing_list', '/mailings/', factory=MailingFactory)
    config.add_route('mailing_add', '/mailing/add/', factory=MailingFactory)
    config.add_route(
        'mailing_edit', '/mailing/{mailing_id}/edit/',
        factory=MailingFactory, traverse='/{mailing_id}'
    )


def add_routes_other(config):
    config.add_route('jvzoo', '/jvzoo/')
    config.add_route('clickbank', '/clickbank/')
    config.add_route('raise_js_error', '/raise-error/js/')
    config.add_route('raise_http_error', '/raise-error/{error_code}/')
    config.add_route('config', '/config/')
    config.add_route('sanitycheck', '/sanity-check/')
    config.add_route('login_as', '/login-as/')
    config.add_route('referrals', '/referrals/')


def register_utilities(config):
    """Register ZCA Utilities to the Pyramid's ZCA registry."""
    # register Sanity Checks
    config.registry.registerUtility(
        sanitycheck.CheckAdminUser,
        sanitycheck.ISanityCheck,
        name='check_admin_user'
    )
    config.registry.registerUtility(
        sanitycheck.CheckDefaultGroups,
        sanitycheck.ISanityCheck,
        name='check_default_groups'
    )
    config.registry.registerUtility(
        sanitycheck.CheckUsersProperties,
        sanitycheck.ISanityCheck,
        name='check_users_properties'
    )
    config.registry.registerUtility(
        sanitycheck.CheckUsersProductGroup,
        sanitycheck.ISanityCheck,
        name='check_users_product_group'
    )
    config.registry.registerUtility(
        sanitycheck.CheckUsersEnabledDisabled,
        sanitycheck.ISanityCheck,
        name='check_users_enabled_disabled'
    )


def kill_connections(username=None, password=None, apiurl=None):
    try:
        r = requests.get(
            '{}/api/connections'.format(apiurl),
            auth=(username, password)
        )
        assert r.status_code == 200

        for connection_dict in r.json():
            name = urllib.quote(connection_dict['name'])
            requests.delete(
                '{}/api/connections/{}'.format(apiurl, name),
                auth=(username, password),
                headers={'X-Reason': 'Auto-kill on app start'}
            )

    except Exception as ex:  # catch everything
        # do not allow errors in this function to stop startup of application
        logger.warning(str(ex))


def add_custom_deform_templates():
    loader = deform.Form.default_renderer.loader
    path = pkg_resources.resource_filename('pyramid_bimt', 'templates')
    loader.search_path = loader.search_path + (path,)


def configure(config, settings={}):

    # Include template renderers
    config.include('pyramid_chameleon')
    config.include('pyramid_mako')

    # Include pyramid layout
    config.include('pyramid_layout')

    # Add route to deform's static resources
    config.add_static_view('deform_static', 'deform:static')

    # Add helpful properties to the request object
    config.set_request_property(
        get_authenticated_user, 'user', reify=True)

    # Setup session factory
    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

    # Set sudo as default permission
    config.set_default_permission(BimtPermissions.sudo)

    # configure routes
    add_routes_auth(config)
    add_routes_user(config)
    add_routes_group(config)
    add_routes_audit_log(config)
    add_routes_portlet(config)
    add_routes_mailing(config)
    add_routes_other(config)

    # register ZCA utilities
    register_utilities(config)

    add_custom_deform_templates()

    # enable views that we need in Robot tests
    ignores = ['pyramid_bimt.tests']
    if asbool(settings.get('robot_testing', 'false')):  # pragma: no cover
        config.add_route('ping', '/ping/')
        config.add_route('robot_commands', '/robot/{command}')
        config.add_tween('pyramid_bimt.testing.inject_js_errorlogger')
        config.add_tween('pyramid_bimt.testing.log_notfound')
    else:
        ignores.append('pyramid_bimt.testing')

    # Run a venusian scan to pick up the declarative configuration.
    config.scan('pyramid_bimt', ignore=ignores)

    if settings.get('bimt.kill_cloudamqp_connections'):  # pragma: no cover
        kill_connections(
            username=settings.get('bimt.amqp_username', ''),
            password=settings.get('bimt.amqp_password', ''),
            apiurl=settings.get('bimt.amqp_apiurl', '')
        )


def check_required_settings(config):
    # make sure default required settings are set
    for setting in REQUIRED_SETTINGS:
        if setting not in config.registry.settings:
            raise KeyError(
                'The "{}" setting is required, please set '
                'it in your .ini file.'.format(setting))

    # make sure production required settings are set
    if config.registry.settings['bimt.mode'] == 'production':
        for setting in REQUIRED_SETTINGS_PRODUCTION:
            if setting not in config.registry.settings:
                raise KeyError(
                    'The "{}" production setting is required, please set '
                    'it in your production.ini file.'.format(setting))


def includeme(config):
    """Allow developers to use ``config.include('pyramid_bimt')``."""

    if 'development.ini' in ' '.join(sys.argv).lower():
        config.registry.settings['bimt.mode'] = Modes.development.name
    elif 'testing.ini' in ' '.join(sys.argv).lower():
        config.registry.settings['bimt.mode'] = Modes.testing.name
    elif 'production.ini' in ' '.join(sys.argv).lower():
        config.registry.settings['bimt.mode'] = Modes.production.name
    else:
        config.registry.settings['bimt.mode'] = Modes.unknown.name
        logger.warning('Unknown mode of operation: {}'.format(
            ' '.join(sys.argv).lower()))

    check_required_settings(config)

    # Setup the DB session and such
    config.include('pyramid_tm')
    config.include('pyramid_basemodel')
    config.include('pyramid_fanstatic')

    # Add support for encrypted session cookies
    config.include('pyramid_beaker')

    # Setup authentication and authorization policies.
    authentication_policy = AuthTktAuthenticationPolicy(
        secret=config.registry.settings['authtkt.secret'],
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
        permission=NO_PERMISSION_REQUIRED,
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
