# -*- coding: utf-8 -*-
"""Mailing models."""

from flufl.enum import Enum
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

import colander
import deform
import logging
import tempfile


logger = logging.getLogger(__name__)


mailing_group_table = Table(
    'mailing_group',
    Base.metadata,
    Column(
        'mailing_id',
        Integer,
        ForeignKey('mailings.id', onupdate="cascade", ondelete="cascade"),
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate="cascade", ondelete="cascade"),
    ),
    UniqueConstraint('mailing_id', 'group_id', name='mailing_id_group_id'),
)

exclude_mailing_group_table = Table(
    'exclude_mailing_group',
    Base.metadata,
    Column(
        'mailing_id',
        Integer,
        ForeignKey('mailings.id', onupdate="cascade", ondelete="cascade"),
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate="cascade", ondelete="cascade"),
    ),
    UniqueConstraint('mailing_id', 'group_id', name='mailing_id_group_id'),
)


MAILING_BODY_DEFAULT = u"""
Enter the main body of the email. It will be injected between the
"Hello <fullname>" and "Best wishes, <app_title> Team".

You can use any user attributes in the email like so: ${user.fullname}
"""


class MailingTriggers(Enum):
    """Supported operators for a mailing"""

    after_created = 'x days after created'
    after_last_payment = 'x days after last_payment'
    before_valid_to = 'x days before valid_to'
    never = 'never'


class Mailing(Base, BaseMixin):
    """A class representing a Mailing."""

    __tablename__ = 'mailings'

    name = Column(
        String,
        unique=True,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Name',
            description='For internal purposes only, not visible to the user.',
            validator=colander.Length(min=2, max=50),
        )},
    )

    groups = relationship(
        'Group',
        secondary=mailing_group_table,
        backref='mailings',
    )

    exclude_groups = relationship(
        'Group',
        secondary=exclude_mailing_group_table,
    )

    trigger = Column(
        SAEnum(*[o.name for o in MailingTriggers], name='triggers'),
        info={'colanderalchemy': dict(
            title='Trigger',
            description='Choose when to send this mailing.',
            widget=deform.widget.SelectWidget(
                values=[(o.name, o.value) for o in MailingTriggers]),
        )},
    )

    days = Column(
        Integer,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Days',
            description='Number of days to send email before/after selected '
            'trigger.',
        )},
    )

    subject = Column(
        Unicode,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Subject',
            description='Enter the subject of the email.',
            validator=colander.Length(min=3, max=100),
        )},
    )

    body = Column(
        Unicode,
        nullable=False,
        default=MAILING_BODY_DEFAULT,
        info={'colanderalchemy': dict(
            title='Body',
            description='Enter the body of the email.',
            widget=deform.widget.TextAreaWidget(rows=10, cols=60),
        )},
    )

    @property
    def allow_unsubscribed(self):
        """False if exclude_groups contains group named unsubscribed."""
        return 'unsubscribed' not in [g.name for g in self.exclude_groups]

    def send(self, recipient):
        """Send the mailing to a recipient."""
        request = get_current_request()
        mailer = get_mailer(request)

        with tempfile.NamedTemporaryFile(suffix='.pt') as body_template:
            assert type(self.body) is unicode, 'Mail body type must be unicode, not {}!'.format(type(self.body))  # noqa
            body_template.write(self.body.encode('utf-8'))
            body_template.seek(0)

            body_template.seek(0)
            body = render(
                body_template.name,
                dict(request=request, user=recipient),
            )

            mailer.send(Message(
                subject=self.subject,
                recipients=[recipient.email, ],
                html=render('pyramid_bimt:templates/email.pt', {
                    'fullname': recipient.fullname,
                    'body': body,
                    'unsubscribe_url': None if self.allow_unsubscribed else request.route_url('user_unsubscribe'),  # noqa
                }),
            ))
            logger.info(u'Mailing "{}" sent to "{}".'.format(
                self.name, recipient.email))

    @classmethod
    def by_id(self, mailing_id):
        """Get a Mailing by id."""
        return Mailing.query.filter_by(id=mailing_id).first()

    @classmethod
    def by_name(self, mailing_name):
        """Get a Mailing by name."""
        return Mailing.query.filter_by(name=mailing_name).first()