# -*- coding: utf-8 -*-
"""Static resources (JS/CSS/images) for BIMT apps."""

from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource
from js.deform import deform_form_css
from js.deform import deform_js
from js.jquery import jquery
from js.jquery_datatables import jquery_datatables_js
from js.jquery_maskedinput import jquery_maskedinput
from js.jquery_timeago import timeago
from js.modernizr import modernizr
from pkg_resources import resource_filename
from pyramid.threadlocal import get_current_registry


import logging

logger = logging.getLogger(__name__)


lib_deform = Library('deform', resource_filename('deform', 'static'))
lib_bimt = Library('pyramid_bimt', 'static')

bootstrap_js = Resource(
    library=lib_bimt,
    relpath='bootstrap.min.js',
    depends=[jquery],
    bottom=True)

bootstrap_css = Resource(
    library=lib_bimt,
    relpath='bootstrap.min.css',
)

bootstrap = Group([bootstrap_js, bootstrap_css])

chosen_js = Resource(
    library=lib_bimt,
    relpath='chosen.jquery.js',
    depends=[jquery],
    bottom=True,
)

chosen_css = Resource(
    library=lib_bimt,
    relpath='chosen.css',
    depends=[bootstrap],
    bottom=True,
)

bimt_css = Resource(
    library=lib_bimt,
    relpath='bimt.css',
    minified='bimt.min.css',
    minifier='cssmin',
    depends=[bootstrap],
)

bimt_js = Resource(
    library=lib_bimt,
    relpath='bimt.js',
    minified='bimt.min.js',
    minifier='jsmin',
    depends=[jquery],
    bottom=True,
)

picker_js = Resource(
    library=lib_deform,
    relpath='pickadate/picker.js',
    minified='pickadate/picker.min.js',
    minifier='jsmin',
    depends=[deform_js],
    bottom=True,
)

fontawesome = Resource(
    library=lib_bimt,
    relpath='font-awesome.css',
    minified='font-awesome.min.css',
    minifier='cssmin',
    depends=[bootstrap],
)

bootbox_js = Resource(
    library=lib_bimt,
    relpath='bootbox.js',
    minified='bootbox.min.js',
    minifier='jsmin',
    depends=[bootstrap],
    bottom=True,
)

chosen_assets = Group([
    chosen_js,
    chosen_css,
])

bimt_assets = Group([
    jquery,
    bootstrap,
    modernizr,
    fontawesome,
    timeago,
    bimt_js,
    bimt_css,
    bootbox_js,
])

base_assets = bimt_assets

table_assets = Group([
    Resource(
        library=lib_bimt,
        relpath='datatables/dataTables.bootstrap.css',
        minified='datatables/dataTables.bootstrap.min.css',
        minifier='cssmin',
        depends=[bootstrap],
    ),
    jquery_datatables_js,
    Resource(
        library=lib_bimt,
        relpath='datatables/dataTables.bootstrap.js',
        minified='datatables/dataTables.bootstrap.min.js',
        minifier='jsmin',
        depends=[jquery_datatables_js],
        bottom=False,
    ),
])

form_assets = Group([
    deform_js,
    jquery_maskedinput,
    Resource(
        library=lib_deform,
        relpath='pickadate/picker.date.js',
        minified='pickadate/picker.date.min.js',
        minifier='jsmin',
        depends=[picker_js],
        bottom=True,
    ),
    Resource(
        library=lib_deform,
        relpath='pickadate/picker.time.js',
        minified='pickadate/picker.time.min.js',
        minifier='jsmin',
        depends=[picker_js],
        bottom=True,
    ),
    deform_form_css,
    Resource(
        library=lib_deform,
        relpath='pickadate/themes/default.css',
        minified='pickadate/themes/default.min.css',
        minifier='cssmin',
        depends=[deform_form_css],
    ),
    Resource(
        library=lib_deform,
        relpath='pickadate/themes/default.date.css',
        minified='pickadate/themes/default.date.min.css',
        minifier='cssmin',
        depends=[deform_form_css],
    ),
    Resource(
        library=lib_deform,
        relpath='pickadate/themes/default.time.css',
        minified='pickadate/themes/default.time.min.css',
        minifier='cssmin',
        depends=[deform_form_css],
    ),
])


class AppAssets(object):  # pragma: no cover
    """Mimick fanstatic's need() call for BIMT app's base assets.

    BIMT never runs alone, it is always a dependency of an app. Each app has
    its own list of static assets. This class helps us find the base group
    of app's assets and calls .need() on them. It does this in a way that
    is syntacticly similar to how you would normally import a fanstatic
    resource and call .need() on it.

    In this way, BIMT view can easily call "app_assets.need()" like it would
    do for any other fanstatic resource and this class will make sure to grab
    the correct assets and require them.
    """

    def need(self):
        app_name = get_current_registry().settings.get('bimt.app_name')
        if not app_name:
            logger.warn('APP_NAME not set, so skipping app_assets.need().')
            return
        app = __import__(app_name)
        assets = getattr(app.static, '{}_assets'.format(app_name))
        assets.need()

app_assets = AppAssets()


def pserve():
    """A pserve script aware of static resources."""
    import pyramid.scripts.pserve
    import pyramid_fanstatic
    import os

    dirname = os.path.dirname(__file__)
    dirname = os.path.join(dirname, 'resources')
    pyramid.scripts.pserve.add_file_callback(
        pyramid_fanstatic.file_callback(dirname))
    pyramid.scripts.pserve.main()
