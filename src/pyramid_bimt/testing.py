# -*- coding: utf-8 -*-
"""Shared/common testing code."""

from collections import deque
from pyramid.exceptions import HTTPNotFound
from pyramid.httpexceptions import WSGIHTTPException
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid_bimt.scripts.populate import add_audit_log_event_types
from pyramid_bimt.scripts.populate import add_demo_auditlog_entries
from pyramid_bimt.scripts.populate import add_demo_mailing
from pyramid_bimt.scripts.populate import add_demo_portlet
from pyramid_bimt.scripts.populate import add_groups
from pyramid_bimt.scripts.populate import add_mailings
from pyramid_bimt.scripts.populate import add_users
from simplejson import JSONDecodeError
from sqlalchemy import create_engine


def initTestingDB(
    auditlog_types=False,
    auditlog_entries=False,
    groups=False,
    users=False,
    portlets=False,
    mailings=False
):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    if auditlog_types:
        add_audit_log_event_types()

    if groups:
        add_groups()

    if users:
        add_users()

    if mailings:
        add_mailings()
        add_demo_mailing()

    if portlets:
        add_demo_portlet()

    if auditlog_entries:
        add_demo_auditlog_entries()


@view_defaults(permission=NO_PERMISSION_REQUIRED)
class RobotAPI(object):  # pragma: no cover
    """HTTP API for Robot Framework tests

    The API is exposed as a set of commands the Robot tests may call in order
    to set up tests with required data.
    """

    def __init__(self, request):
        self.request = request

    @view_config(
        route_name='robot_commands',
        renderer='json',
        request_method='POST',
        http_cache=0,
    )
    def __call__(self):
        """API entry point.

        .. http:post:: /robot/(command)

            The :http:method:`POST` body must be a JSON object containing the
            arguments corresponding to the command.

            The response body contains a JSON object with at least a key
            `result` with the value `ok` if the command was successfully
            completed. The object may contain additional fields depending on
            the command, e.g.

            .. code-block:: javascript

                {
                    'result': 'ok',
                    'username': 'foo',
                    'email': 'foo@bar.com'
                }

            :param command:  The command to perform.

            :status 200: Command completed. Check the response body for status.

            Example request

            .. sourcecode:: http

                POST /robot/reset_notfound HTTP/1.1
                Host: localhost
                Accept: application/json

                {
                  'username': 'foobar'
                }

            Example response

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Content-Type: application/json

                {
                  'status' : 'ok'
                }

        """
        method_name = 'cmd_{}'.format(self.request.matchdict.get('command'))
        cmd = getattr(self, method_name)
        if cmd is None:  # pragma: no cover
            return HTTPNotFound
        try:
            data = self.request.json
        except JSONDecodeError:
            data = None
        return cmd(data)

    def cmd_app_name(self, data):
        """Return app name."""
        return self.request.registry.settings['bimt.app_name']

    def cmd_app_title(self, data):
        """Return app title."""
        return self.request.registry.settings['bimt.app_title']

    def cmd_app_domain(self, data):
        """Return app domain."""
        return self.request.registry.settings['bimt.app_domain']

    def cmd_list_notfound(self, data):
        """List 404-not-found errors."""
        status = 'ok'
        if notfound_info:
            status = 'error'
        return {
            'result': status,
            'errors': tuple(notfound_info)
        }

    def cmd_reset_notfound(self, data):
        """Reset the list of 404-not-found errors."""
        notfound_info.clear()
        return dict(result='ok')

    def cmd_list_js_exceptions(self, data):
        """List JS errors."""
        status = 'ok'
        if js_exceptions:
            status = 'error'
        return {
            'result': status,
            'errors': tuple(js_exceptions)
        }

    def cmd_log_js_exception(self, data):
        """Log a JS error."""
        js_exceptions.append(data)
        return dict(result='ok')

    def cmd_reset_js_exceptions(self, data):
        """Reset list of JS errors."""
        js_exceptions.clear()
        return dict(result='ok')


notfound_info = deque()
js_exceptions = deque()


def log_notfound(handler, registry):  # pragma: no cover
    def log_notfound_tween(request):
        response = handler(request)
        if response.content_type == 'text/html':
            if u'page you were trying to view does not exist' in response.text:
                notfound_info.append({
                    'url': request.url,
                    'referrer': request.referrer
                })
        return response
    return log_notfound_tween


def inject_js_errorlogger(handler, registry):  # pragma: no cover
    def inject_js_errorlogger_tween(request):
        response = handler(request)
        if response.content_type == 'text/html':
            if isinstance(response, WSGIHTTPException):
                # the body of a WSGIHTTPException needs to be 'prepared'
                response.prepare(request.environ)
            tag = """
            <script>
                window.onerror = function(message, file, line) {
                    $.ajax({
                        url: '/robot/log_js_exception',
                        contentType: 'application/json',
                        processData: false,
                        type: 'POST',
                        data: JSON.stringify(
                            {message: message, file: file, line: line})
                    });
                };
                </script>
            """
            content = response.body.replace('<head>', '<head>\n' + tag)
            response.app_iter = [content]
            response.content_length = len(content)
        return response
    return inject_js_errorlogger_tween
