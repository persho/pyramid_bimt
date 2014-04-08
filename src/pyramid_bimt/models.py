# -*- coding: utf-8 -*-
"""Define models."""

from datetime import date
from flufl.enum import Enum
from pyramid.renderers import render
from pyramid.threadlocal import get_current_request
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_basemodel import Session
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
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

_marker = object()


user_group_table = Table(
    'user_group',
    Base.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    UniqueConstraint('user_id', 'group_id', name='user_id_group_id'),
)


class Group(Base, BaseMixin):
    """A class representing a Group."""

    __tablename__ = 'groups'

    name = Column(
        String,
        unique=True,
    )

    product_id = Column(
        Integer,
        unique=True,
        nullable=True,
        info={'colanderalchemy': dict(
            title='JVZoo Product ID',
            description='If this group is tied to a JVZoo product, enter its '
            'ID here.'
        )},
    )

    validity = Column(
        Integer,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Validity Days',
            description='Number of days to extend valid_to when a user from '
            'this group makes a payment',
        )},
    )

    trial_validity = Column(
        Integer,
        nullable=True,
        info={'colanderalchemy': dict(
            title='Validity Days for Trial',
            description='If greater than "0" then members of this group will '
            'first be put in the trial group and their valid_to will be set '
            'to this amount of days in the future.',
        )},
    )

    @classmethod
    def by_id(self, group_id):
        """Get a Group by id."""
        return Group.query.filter_by(id=group_id).first()

    @classmethod
    def by_name(self, name):
        """Get a Group by name."""
        return Group.query.filter_by(name=name).first()

    @classmethod
    def by_product_id(self, product_id):
        """Get a Group by product_id."""
        return Group.query.filter_by(product_id=product_id).first()

    @classmethod
    def get_all(class_, order_by='name', filter_by=None, limit=1000):
        """Return all groups.

        filter_by: dict -> {'name': 'foo'}

        By default, order by Group.name.
        """
        Group = class_
        q = Group.query
        q = q.order_by(getattr(Group, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q


class UserProperty(Base, BaseMixin):
    """A key value store for user properties."""

    __tablename__ = 'user_properties'

    UniqueConstraint('key', 'user_id', name='key_user_id')

    #: unique for any key + user_id combination
    key = Column(
        String,
        unique=False,
        nullable=False,
    )

    #: value for the given key
    value = Column(Unicode)

    #: user id of the owner of this property
    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )


class User(Base, BaseMixin):
    """A class representing a User."""

    __tablename__ = 'users'

    #: used for logging in and system emails
    email = Column(
        String,
        unique=True,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Email',
        )}
    )

    #: encrypted with passlib
    password = Column(
        Unicode(120),
        info={'colanderalchemy': dict(
            title='Password',
            widget=deform.widget.PasswordWidget(size=128),
        )}
    )

    #: unicode fullname, used in UI and emails
    fullname = Column(
        Unicode(120),
        info={'colanderalchemy': dict(
            title='Full name',
        )}
    )

    #: email of the affiliate that referred this user
    affiliate = Column(
        Unicode,
        info={'colanderalchemy': dict(
            title='Affiliate',
        )}
    )

    #: (optional) email that is used to make paypal purchases, if different
    #: than login email
    billing_email = Column(
        String,
        unique=True,
        info={'colanderalchemy': dict(
            title='Billing Email',
        )}
    )

    #: date until user's subscription is valid, after this date the
    #: :func:`expire_subscriptions
    #: <pyramid_bimt.scripts.expire_subscriptions.expire_subscriptions>` will
    #: disable the user
    valid_to = Column(
        Date,
        default=date.today,
        info={'colanderalchemy': dict(
            title='Valid To',
        )},
    )

    #: (optional) Date on which user made his latest payment
    last_payment = Column(
        Date,
        info={'colanderalchemy': dict(
            title='Last payment',
        )},
    )

    #: shorthand for accessing user's groups
    groups = relationship(
        'Group', secondary=user_group_table, backref='users')

    #: shorthand for accessing user's properties
    properties = relationship(
        'UserProperty', cascade='all,delete-orphan')

    #: shorthand for accessing user's auditlog entries
    audit_log_entries = relationship(
        'AuditLogEntry', backref='user')

    def get_property(self, key, default=_marker):
        """Get a User's property by key.

        :param key: Key by which to find the property.
        :type key: Unicode
        :param default: The return value if no property is found. Raises
            ValueError by default.
        :type default: anything
        :return: value of the property
        :rtype: Unicode
        """
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1:
            if default == _marker:
                raise KeyError(u'Property "{}" not found.'.format(key))
            else:
                return default
        return result.one().value

    def set_property(self, key, value, strict=False):
        """Set a User's property by key.

        :param key: Key by which to save the property.
        :type key: Unicode
        :param value: Value of the property.
        :type value: Unicode
        :param strict: If True, raise an error if property of given key key
            does not yet exists. In other words, update an existing property or
            fail. False by default.
        :type strict: bool
        """
        result = UserProperty.query.filter_by(user_id=self.id, key=key)
        if result.count() < 1 and strict:
            raise KeyError('Property "{}" not found.'.format(key))
        elif result.count() < 1 and not strict:
            self.properties.append(UserProperty(key=key, value=value))
        else:
            result.one().value = value

    @property
    def admin(self):
        """True if User is in 'admins' group, False otherwise."""
        return 'admins' in [g.name for g in self.groups]

    @property
    def trial(self):
        """True if User is in 'trial' group, False otherwise."""
        return 'trial' in [g.name for g in self.groups]

    @property
    def enabled(self):
        """True if User is in 'enabled' group, False otherwise."""
        return 'enabled' in [g.name for g in self.groups]

    def enable(self):
        """Enable User by putting it in the 'enabled' group.

        :return: True if user was enabled, False if nothing changed.
        :rtype: bool
        """
        if not self.enabled:
            self.groups.append(Group.by_name('enabled'))
            return True
        else:
            return False

    def disable(self):
        """Disable User by removing it from the 'enabled' group.

        :return: True if user was disabled, False if nothing changed.
        :rtype: bool
        """
        if self.enabled:
            self.groups.remove(Group.by_name('enabled'))
            return True
        else:
            return False

    @classmethod
    def by_id(self, user_id):
        """Get a User by id."""
        return User.query.filter_by(id=user_id).first()

    @classmethod
    def by_email(self, email):
        """Get a User by email."""
        return User.query.filter_by(email=email).first()

    @classmethod
    def by_billing_email(self, billing_email):
        """Get a User by billing email."""
        return User.query.filter_by(billing_email=billing_email).first()

    @classmethod
    def get_all(class_, order_by='email', filter_by=None, limit=1000):
        """Return all users.

        filter_by: dict -> {'name': 'foo'}

        By default, order by User.email.
        """
        User = class_
        q = User.query
        q = q.order_by(getattr(User, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q

    @classmethod
    def get_enabled(self):
        enabled = Group.by_name('enabled')
        return User.query.filter(User.groups.contains(enabled)).all()


class AuditLogEventType(Base):
    """A class representing an Audit log event type."""

    __tablename__ = 'audit_log_event_types'

    entries = relationship('AuditLogEntry', backref='event_type')

    id = Column(
        Integer,
        primary_key=True,
    )

    #: string, name of the event type
    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    #: unicode, for UI display
    title = Column(
        Unicode,
    )

    #: unicode, for UI display
    description = Column(
        Unicode,
    )

    @classmethod
    def by_name(self, name):
        """Get an auditlog event type by name.

        A convenience method for getting an ``AuditLogEventType`` by name.
        Normally you need this when adding a new :class:`AuditLogEntry
        <pyramid_bimt.models.AuditLogEntry>` and you need to set its
        :attr:`event type <pyramid_bimt.models.AuditLogEntry.event_type_id>`:

        .. code-block:: python

            AuditLogEntry(
                user_id=user.id,
                event_type_id=AuditLogEventType.by_name('UserEnabled').id,
            )

        :param name: Name of the ``AuditLogEventType`` you want to get.
        :type name: string

        :return: ``AuditLogEventType`` object of the given name
        :rtype: instance of ``AuditLogEventType``
        """
        return Session.query(AuditLogEventType).filter_by(name=name).first()

    @classmethod
    def by_id(self, id):
        """Get an auditlog event type by id.

        :param name: ID of the ``AuditLogEventType`` you want to get.
        :type name: int

        :return: ``AuditLogEventType`` object of the given id
        :rtype: instance of ``AuditLogEventType``
        """
        return Session.query(AuditLogEventType).filter_by(id=id).first()

    @classmethod
    def get_all(class_, order_by='name', filter_by=None, limit=100):
        """Return all auditlog event types.

        :param order_by: The column name that should be used for ordering
            results.
        :type order_by: string

        :param filter_by: Mapping of query filters, for example
            ``{'description': 'foo'}``
        :type filter_by: dict

        :return: list of AuditLogEventType instances, wrapped in a SQLAlchemy
            Query object, so you can call ``.all()`` to convert to list, or
            append additional query parameters (such as ``.desc()`` for
            descending)
        :rtype: :class:sqlalchemy.orm.query.Query
        """
        AuditLogEventType = class_
        q = Session.query(AuditLogEventType)
        q = q.order_by(getattr(AuditLogEventType, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q


@colander.deferred
def users_select_widget(node, kw):
    users = User.get_all()
    choices = [(user.id, user.email) for user in users]
    return deform.widget.SelectWidget(values=choices)


@colander.deferred
def event_types_select_widget(node, kw):
    types = AuditLogEventType.get_all()
    choices = [(type_.id, type_.name) for type_ in types]
    return deform.widget.SelectWidget(values=choices)


class AuditLogEntry(Base):
    __tablename__ = 'audit_log_entries'

    id = Column(
        Integer,
        primary_key=True,
    )

    #: id of user that triggered the entry
    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        info={'colanderalchemy': dict(
            title='User ID',
            # TODO: Make values dynamic, not read at startup
            widget=users_select_widget,
        )}
    )

    #: entry AuditLogEventType id
    event_type_id = Column(
        Integer,
        ForeignKey('audit_log_event_types.id'),
        info={'colanderalchemy': dict(
            title='Event Type ID',
            # TODO: Make values dynamic, not read at startup
            widget=event_types_select_widget
        )}
    )

    #: when was the entry triggered
    timestamp = Column(
        DateTime,
        info={'colanderalchemy': dict(title='Timestamp')}
    )

    #: (optional) additional information about the entry
    comment = Column(
        Unicode,
        info={'colanderalchemy': dict(
            title='Comment',
            missing=u'Manual audit log entry',
        )}
    )

    @classmethod
    def by_id(self, id):
        """Get an AuditLogEntry by id."""
        return Session.query(AuditLogEntry).filter_by(id=id).first()

    @classmethod
    def get_all(class_, order_by='timestamp', filter_by=None, limit=100):
        """Return all auditlog entries.

        By default, order by ``timestamp`` and limit to ``100`` results.

        :param order_by: The column name that should be used for ordering
            results.
        :type order_by: string

        :param order_by: Mapping of query filters, for example
            ``{'comment': 'foo'}``
        :type order_by: dict

        :return: list of AuditLogEntry instances, wrapped in a SQLAlchemy Query
            object, so you can call ``.all()`` to convert to list, or append
            additional query parameters (such as ``.desc()`` for descending)
        :rtype: :class:sqlalchemy.orm.query.Query
        """
        AuditLogEntry = class_
        q = Session.query(AuditLogEntry)
        q = q.order_by(getattr(AuditLogEntry, order_by).desc())
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q


portlet_group_table = Table(
    'portlet_group',
    Base.metadata,
    Column(
        'portlet_id',
        Integer,
        ForeignKey('portlets.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate="cascade", ondelete="cascade"),
        primary_key=True,
    ),
    UniqueConstraint('portlet_id', 'group_id', name='portlet_id_group_id'),
)


class PortletPositions(Enum):
    """Supported positions for portlets"""

    #: display a portlet in the main content area, next to the sidebar, just
    #: before any othercontent
    above_content = 'Above Content'

    #: display a portlet in the sidebar column, below any other sidebar content
    below_sidebar = 'Below Sidebar'

    #: display a portlet in the footer row, full-width, before any other footer
    #: content
    above_footer = 'Above Footer'


class Portlet(Base, BaseMixin):
    """A class representing a Portlet."""

    __tablename__ = 'portlets'

    name = Column(
        String,
        unique=True,
        nullable=False,
        info={'colanderalchemy': dict(
            title='Name',
            description='For internal use only, not visible to the user.',
            validator=colander.Length(min=2, max=50),
        )},
    )

    groups = relationship(
        'Group',
        secondary=portlet_group_table,
        backref='portlets',
    )

    position = Column(
        SAEnum(*[p.name for p in PortletPositions], name='positions'),
        info={'colanderalchemy': dict(
            title='Position',
            description='Choose where to show this portlet.',
            widget=deform.widget.SelectWidget(
                values=[(p.name, p.value) for p in PortletPositions]),
        )},
    )

    weight = Column(
        Integer,
        default=0,
        info={'colanderalchemy': dict(
            title='Weight',
            description='The higher the number the higher the portlet will be '
            'positioned (range from -128 to 127).',
            validator=colander.Range(-128, 127),
        )},
    )

    html = Column(
        Unicode,
        default=u'',
        info={'colanderalchemy': dict(
            title='HTML code',
            description='The HTML code that will be shown for this portlet.',
            widget=deform.widget.TextAreaWidget(rows=10),
        )},
    )

    @classmethod
    def by_id(self, portlet_id):
        """Get a Portlet by id."""
        return Portlet.query.filter_by(id=portlet_id).first()

    @classmethod
    def by_user_and_position(self, user, position):
        """Get all portlets that are visible to a user."""
        portlets = Portlet.query.filter(Portlet.position == position) \
            .order_by(Portlet.weight.desc())

        def any_group(groups1, groups2):
            for group1 in groups1:
                if group1 in groups2:
                    return True
            return False
        return [p for p in portlets if any_group(user.groups, p.groups)]

    @classmethod
    def get_all(class_, order_by='position', filter_by=None, limit=100):
        """Return all Portlets.

        filter_by: dict -> {'name': 'foo'}

        By default, order by Portlet.position.
        """
        Portlet = class_
        q = Portlet.query
        q = q.order_by(getattr(Portlet, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        q = q.limit(limit)
        return q.all()


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

    def send(self, recipient):
        """Send the mailing to a recipient."""
        request = get_current_request()
        mailer = get_mailer(request)

        with tempfile.NamedTemporaryFile(suffix='.pt') as body_template:
            body_template.write(self.body)
            body_template.seek(0)

            body_template.seek(0)
            body = render(
                body_template.name,
                dict(request=request, user=recipient),
            )

            mailer.send(Message(
                subject=self.subject,
                recipients=[recipient.email, ],
                html=render(
                    'pyramid_bimt:templates/email.pt',
                    {'fullname': recipient.fullname, 'body': body}),
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
