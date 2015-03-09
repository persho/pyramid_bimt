# -*- coding: utf-8 -*-
"""Send referral emails."""

from deform import Button
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid_bimt.const import BimtPermissions
from pyramid_bimt.events import ReferralEmailSent
from pyramid_bimt.views import FormView
from pyramid_deform import CSRFSchema
from pyramid_mailer.mailer import Mailer
from pyramid_mailer.message import Message

import colander
import deform


def emails_validator(node, value):
    value = value.lower()
    for email in value.splitlines():
        colander.Email()(node, email)


class ReferralsSchema(CSRFSchema, colander.MappingSchema):
    emails = colander.SchemaNode(
        colander.String(),
        validator=emails_validator,
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),
        description='Enter emails of friends you want to invite. '
                    ' One email per line.'
    )


@view_config(
    route_name='referrals',
    permission=BimtPermissions.view,
    layout='default',
    renderer='pyramid_bimt:templates/referrals.pt',
)
class ReferralsView(FormView):
    schema = ReferralsSchema()
    buttons = (Button(name='send_invites', title=u'Send Invites'), )
    title = 'Send Referral Invites'
    form_options = (('formid', 'login_as'), ('method', 'POST'))

    def send_invites_success(self, appstruct):
        settings = self.request.registry.settings
        mailer = Mailer(
            host=settings['mail.host'],
            port=settings['mail.port'],
            username=settings['bimt.referrals_mail_username'],
            password=settings['bimt.referrals_mail_password'],
            tls=True,
            default_sender=settings['bimt.referrals_mail_sender'],
        )
        emails = appstruct['emails'].splitlines()
        for email in emails:
            mailer.send(Message(
                subject=u'Your friend, {}, gave you exclusive access to {}'.format(  # noqa
                    self.request.user.fullname, settings['bimt.app_title']),
                recipients=[email, ],
                html=render(
                    'pyramid_bimt:templates/referral_email.pt',
                    {'request': self.request}
                ))
            )
            self.request.registry.notify(
                ReferralEmailSent(
                    self.request,
                    self.request.user,
                    'Referral email sent to: {}'.format(email)
                )
            )

        self.request.session.flash(u'Referral email sent to: {}'.format(
            ', '.join(appstruct['emails'].splitlines()))
        )
        return HTTPFound(location=self.request.route_path('referrals'))
