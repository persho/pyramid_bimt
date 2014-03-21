# -*- coding: utf-8 -*-
"""Manage mailings."""

from colanderalchemy import SQLAlchemySchemaNode
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid_basemodel import Session
from pyramid_bimt.models import Group
from pyramid_bimt.models import Mailing
from pyramid_bimt.models import MailingTriggers
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import table_assets
from pyramid_bimt.views import FormView
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

import colander
import deform
import tempfile


class MailingView(object):
    def __init__(self, context, request):
        self.request = request
        self.context = context
        app_assets.need()

    @view_config(
        route_name='mailing_list',
        permission='admin',
        layout='default',
        renderer='pyramid_bimt:templates/mailings.pt',
    )
    def list(self):
        self.request.layout_manager.layout.hide_sidebar = True
        table_assets.need()

        return {
            'triggers': MailingTriggers,
            'mailings': Mailing.query.order_by(Mailing.name).all(),
        }


@view_config(
    route_name='mailing_add',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class MailingAdd(FormView):
    buttons = ('submit', )
    title = 'Add Mailing'
    form_options = (('formid', 'mailing-add'), ('method', 'POST'))
    fields = [
        'name',
        'trigger',
        'days',
        'subject',
        'body',
    ]

    def __init__(self, request):
        self.request = request
        self.schema = SQLAlchemySchemaNode(Mailing, includes=self.fields)

        # we don't like the way ColanderAlchemy renders SA Relationships so
        # we manually inject a suitable SchemaNode for groups
        choices = [(group.id, group.name) for group in Group.get_all()]
        self.schema.add_before(
            'trigger',
            node=colander.SchemaNode(
                colander.Set(),
                name='groups',
                missing=[],
                widget=deform.widget.CheckboxChoiceWidget(values=choices),
            ),
        )

    def submit_success(self, appstruct):
        mailing = Mailing(
            name=appstruct['name'],
            groups=[Group.by_id(group_id) for group_id in appstruct.get('groups')],  # noqa
            trigger=appstruct['trigger'],
            days=appstruct['days'],
            subject=appstruct['subject'],
            body=appstruct['body'],
        )

        Session.add(mailing)
        Session.flush()
        self.request.session.flash(u'Mailing "{}" added.'.format(mailing.name))
        return HTTPFound(
            location=self.request.route_path(
                'mailing_edit', mailing_id=mailing.id))

    def appstruct(self):
        appstruct = dict()
        for field in self.fields + ['groups']:
            if self.request.params.get(field) is not None:
                appstruct[field] = self.request.params[field]

        return appstruct


@view_config(
    route_name='mailing_edit',
    layout='default',
    permission='admin',
    renderer='pyramid_bimt:templates/form.pt',
)
class MailingEdit(MailingAdd):
    buttons = (
        'save',
        deform.Button(
            name='test',
            css_class='btn-success',
        ),
        deform.Button(
            name='send immediately',
            css_class='btn-warning btn-confirmation'
        ),
    )
    title = 'Edit Mailing'
    form_options = (('formid', 'mailing-edit'), ('method', 'POST'))

    def before(self, form):
        """Override value of `send immediately` button."""
        mailing = self.request.context
        for button in form.buttons:
            if button.name == 'send_immediately':
                button.value = 'Immediately send mailing "{}" to all {} ' \
                    'recipients without date constraints?'.format(
                        mailing.name, len(self.recipients))

    @property
    def recipients(self):
        """Return a list of recipients for this mailing."""
        mailing = self.request.context

        recipients = set()
        for group in mailing.groups:
            recipients = recipients.union(group.users)
        return recipients

    def save_success(self, appstruct):
        mailing = self.request.context

        mailing.name = appstruct['name']
        mailing.groups = [Group.by_id(group_id) for group_id in appstruct['groups']]  # noqa
        mailing.trigger = appstruct['trigger']
        mailing.days = appstruct['days']
        mailing.subject = appstruct['subject']
        mailing.body = appstruct['body']

        self.request.session.flash(
            u'Mailing "{}" modified.'.format(mailing.name))
        return HTTPFound(
            location=self.request.route_path(
                'mailing_edit', mailing_id=mailing.id))

    def test_success(self, appstruct):
        mailing = self.request.context

        with tempfile.NamedTemporaryFile(suffix='.pt') as template:
            template.write(mailing.body)
            template.seek(0)
            body = render(
                template.name,
                {'request': self.request, 'user': self.request.user},
            )

        # prepend a list of recipients that would receive this mailing in
        # a non-test run
        prefix = u"""
        This mailing would be sent to: <br />
        {} <br />
        ------------------ <br /><br />
        """.format('<br />'.join([r.email for r in self.recipients]))
        body = prefix + body

        mailer = get_mailer(self.request)
        mailer.send(Message(
            subject=u'[Mailing Test] {}'.format(mailing.subject),
            recipients=[self.request.user.email, ],
            html=render(
                'pyramid_bimt:templates/email.pt',
                {'fullname': self.request.user.fullname, 'body': body}),
        ))

        self.request.session.flash(
            u'Mailing "{}" sent to "{}".'.format(
                mailing.name, self.request.user.email))
        return HTTPFound(
            location=self.request.route_path(
                'mailing_edit', mailing_id=mailing.id))

    def send_immediately_success(self, appstruct):
        mailing = self.request.context

        for recipient in self.recipients:
            mailing.send(recipient)

        self.request.session.flash(
            u'Mailing "{}" sent to {} recipients.'.format(
                mailing.name, len(self.recipients)))
        return HTTPFound(
            location=self.request.route_path(
                'mailing_edit', mailing_id=mailing.id))

    def appstruct(self):
        context = self.request.context
        appstruct = dict()
        for field in self.fields:
            if (
                hasattr(context, field) and
                getattr(context, field) is not None
            ):
                appstruct[field] = getattr(context, field)

        if context.groups:
            appstruct['groups'] = [str(g.id) for g in context.groups]

        return appstruct