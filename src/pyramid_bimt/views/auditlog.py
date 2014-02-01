# -*- coding: utf-8 -*-
"""Views for loggin in, logging out, etc."""

from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_bimt.static import table_assets
from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_basemodel import Session
from pyramid_bimt.models import AuditLogEntry
from pyramid_deform import FormView


@view_config(
    route_name='audit_log',
    permission='admin',
    layout='default',
    renderer='pyramid_bimt:templates/audit_log.pt',
)
def audit_log(request):
    request.layout_manager.layout.hide_sidebar = True
    app_assets.need()
    table_assets.need()
    return {
        'entries': AuditLogEntry.get_all(),
    }


@view_config(
    route_name='audit_log_delete',
    permission='admin',
)
def audit_log_delete(request):
    entry = request.context
    Session.delete(entry)
    request.session.flash(u'Audit log entry deleted.')
    return HTTPFound(location=request.route_path('audit_log'))


@view_config(
    route_name='audit_log_add',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class AuditLogAddEntryForm(FormView):
    schema = SQLAlchemySchemaNode(
        AuditLogEntry,
        includes=['timestamp', 'user_id', 'event_type_id', 'comment']
    )
    buttons = ('submit', )
    title = 'Add Audit log entry'
    form_options = (('formid', 'login'), ('method', 'POST'))

    def __call__(self):
        app_assets.need()
        form_assets.need()
        result = super(AuditLogAddEntryForm, self).__call__()
        if isinstance(result, dict):  # pragma: no cover
            result['title'] = self.title
        return result

    def submit_success(self, appstruct):
        entry = AuditLogEntry(
            timestamp=appstruct['timestamp'],
            user_id=appstruct['user_id'],
            event_type_id=appstruct['event_type_id'],
            comment=appstruct['comment'],
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
        }
