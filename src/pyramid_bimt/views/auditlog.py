# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from collections import OrderedDict
from datetime import datetime
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_basemodel import Session
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.models import AuditLogEntry
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import chosen_assets
from pyramid_bimt.static import form_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import DatatablesDataView
from pyramid_bimt.views import SQLAlchemySchemaNode
from pyramid_deform import FormView

import logging

logger = logging.getLogger(__name__)


@view_config(
    route_name='audit_log',
    permission=BimtPermissions.view,
    layout='default',
    renderer='pyramid_bimt:templates/audit_log.pt',
    xhr=False,
)
def audit_log(request):
    request.layout_manager.layout.hide_sidebar = True
    request.layout_manager.layout.title = u'Activity'
    app_assets.need()
    table_assets.need()

    new = AuditLogEntry.get_all(
        request=request,
        filter_by={'read': False}
    ).count()
    if new:  # pragma: no branch
        request.session.flash('{} new notifications.'.format(new))

    return {}


@view_config(
    route_name='audit_log',
    permission=BimtPermissions.view,
    renderer='json',
    xhr=True,
)
class AuditLogAJAX(DatatablesDataView):
    """Ajax view used to populate AuditLog datatables with JSON data."""
    model = AuditLogEntry

    columns = OrderedDict()
    columns['timestamp'] = None
    columns['event_type_id'] = None
    columns['user_id'] = None
    columns['comment'] = None
    columns['action'] = None

    def populate_columns(self, entry):
        if not entry.read and self.request.user == entry.user:
            self.columns['DT_RowClass'] = 'active'
            entry.read = True

        self.columns['event_type_id'] = entry.event_type.title
        self.columns['comment'] = entry.comment

        timestamp = entry.timestamp.strftime('%Y/%m/%d %H:%M:%S')
        self.columns['timestamp'] = """
            <time class="timeago" datetime="{}Z">{} UTC</time>
            """.format(timestamp, timestamp)

        if entry.user:
            self.columns['user_id'] = '<a href="{}">{}</a>'.format(
                self.request.route_path('user_view', user_id=entry.user.id),
                entry.user.email,
            )

        if self.request.has_permission(BimtPermissions.manage):
            self.columns['action'] = """
            <a class="btn btn-xs btn-danger" href="{}">
              <span class="glyphicon glyphicon-remove-sign"></span> Delete
            </a>
            """.format(
                self.request.route_path('audit_log_delete', entry_id=entry.id))
        else:
            self.columns['action'] = None


@view_config(
    route_name='audit_log_read_all',
    permission=BimtPermissions.view,
)
def audit_log_read_all(request):
    for entry in AuditLogEntry.get_all(
        request=request,
        filter_by={'read': False}
    ):
        entry.read = True
    request.session.flash(u'All activity entries marked as read.')
    return HTTPFound(location=request.route_path('audit_log'))


@view_config(
    route_name='audit_log_delete',
    permission=BimtPermissions.manage,
)
def audit_log_delete(request):
    entry = request.context
    Session.delete(entry)
    logger.info(u'User {} removing auditlog entry {}.'.format(
        request.user, entry))
    request.session.flash(u'Audit log entry deleted.')
    return HTTPFound(location=request.route_path('audit_log'))


@view_config(
    route_name='audit_log_add',
    layout='default',
    permission=BimtPermissions.manage,
    renderer='pyramid_bimt:templates/form.pt',
)
class AuditLogAddEntryForm(FormView):
    schema = SQLAlchemySchemaNode(
        AuditLogEntry,
        includes=['timestamp', 'user_id', 'event_type_id', 'comment', 'read']
    )
    buttons = ('submit', )
    title = 'Add Audit log entry'
    form_options = (('formid', 'login'), ('method', 'POST'))

    def __call__(self):
        app_assets.need()
        form_assets.need()
        chosen_assets.need()
        result = super(AuditLogAddEntryForm, self).__call__()
        if isinstance(result, dict):  # pragma: no cover
            result['title'] = self.title
        return result

    def submit_success(self, appstruct):
        entry = AuditLogEntry(
            timestamp=appstruct.get('timestamp') or datetime.utcnow(),
            user_id=appstruct['user_id'],
            event_type_id=appstruct['event_type_id'],
            comment=appstruct['comment'],
            read=appstruct['read'],
        )
        Session.add(entry)
        self.request.session.flash(u'Audit log entry added.')
        return HTTPFound(location=self.request.route_path('audit_log'))

    def appstruct(self):
        return {
            'timestamp': self.request.params.get('timestamp', None),
            'user_id': self.request.params.get('user_id', 0),
            'event_type_id': self.request.params.get('event_type_id', 0),
            'comment': self.request.params.get('comment', ''),
            'read': self.request.params.get('read', False),
        }
