# -*- coding: utf-8 -*-
"""misc and tool views, etc."""

from pyramid.httpexceptions import exception_response
from pyramid.view import view_config
from datetime import datetime
from pyramid.response import Response


@view_config(
    route_name='raise_http_error',
    permission='admin',
)
def raise_http_error(request):
    raise exception_response(int(request.matchdict['error_code']))


@view_config(
    route_name='raise_js_error',
    permission='admin',
)
def raise_js_error(request):
    body = """<script type="text/javascript">
      throw new Error('[{now}] Error test.');
    </script>

    <p>[{now}] Error test.</p>""".format(now=datetime.utcnow())
    return Response(
        content_type='text/html',
        body=body
    )
