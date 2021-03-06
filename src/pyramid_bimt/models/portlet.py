# -*- coding: utf-8 -*-
"""Portlet models."""


from flufl.enum import Enum
from pyramid.renderers import render
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid_bimt.models import GetByIdMixin
from pyramid_bimt.models import GetByNameMixin
from pyramid_bimt.widgets import ChosenSelectWidget
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


portlet_group_table = Table(
    'portlet_group',
    Base.metadata,
    Column(
        'portlet_id',
        Integer,
        ForeignKey('portlets.id', onupdate='cascade', ondelete='cascade'),
        primary_key=True,
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate='cascade', ondelete='cascade'),
        primary_key=True,
    ),
    UniqueConstraint('portlet_id', 'group_id', name='portlet_id_group_id'),
)

exclude_portlet_group_table = Table(
    'exclude_portlet_group',
    Base.metadata,
    Column(
        'portlet_id',
        Integer,
        ForeignKey('portlets.id', onupdate='cascade', ondelete='cascade'),
    ),
    Column(
        'group_id',
        Integer,
        ForeignKey('groups.id', onupdate='cascade', ondelete='cascade'),
    ),
    UniqueConstraint('portlet_id', 'group_id', name='exclude_portlet_id_group_id'),  # noqa
)


class PortletPositions(Enum):
    """Supported positions for portlets."""

    #: Display a portlet in the main content area, next to the sidebar, just
    #: before any othercontent.
    above_content = 'Above Content'

    #: Display a portlet in the sidebar column, below any other sidebar
    #: content.
    below_sidebar = 'Below Sidebar'

    #: Display a portlet in the sidebar column, above any other sidebar
    #: content.
    above_sidebar = 'Above Sidebar'

    #: Display a portlet in the footer row, full-width, before any other footer
    #: content.
    above_footer = 'Above Footer'


class Portlet(Base, BaseMixin, GetByIdMixin, GetByNameMixin):
    """A class representing a Portlet.

    Portlets are small bits of HTML that are injected in header, sidebar
    or footer. They are managed TTW by Staff members.
    """

    __tablename__ = 'portlets'

    #: Name of the portlet, for internal use only.
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

    #: Groups for which this portlet is displayed.
    groups = relationship(
        'Group',
        secondary=portlet_group_table,
        backref='portlets',
    )

    #: Groups for which this portlet is not displayed.
    exclude_groups = relationship(
        'Group',
        secondary=exclude_portlet_group_table,
    )

    #: Position where this portlet is displayed.
    position = Column(
        SAEnum(*[_p.name for _p in PortletPositions], name='positions'),
        info={'colanderalchemy': dict(
            title='Position',
            description='Choose where to show this portlet.',
            widget=ChosenSelectWidget(
                values=[(_p.name, _p.value) for _p in PortletPositions]),
        )},
    )

    #: Used for ordering portlets. The higher the weight, the higher the
    #: portlet will be displayed, in relation to other portlets in the same
    #: position.
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

    #: The body of the portlet.
    html = Column(
        Unicode,
        default=u'',
        info={'colanderalchemy': dict(
            title='HTML code',
            description='The HTML code that will be shown for this portlet.',
            widget=deform.widget.TextAreaWidget(rows=10),
        )},
    )

    def __repr__(self):
        """Custom representation of the Portlet object."""
        return u'<{}:{} (name={})>'.format(
            self.__class__.__name__, self.id, repr(self.name))

    def get_rendered_portlet(self):
        """Get rendered portlet html."""
        return render(
            'pyramid_bimt:templates/portlet.pt',
            {'content': self.html}
        )

    @classmethod
    def by_user_and_position(cls, user, position):
        """Get all portlets that are visible to a user."""
        portlets = Portlet.query.filter(Portlet.position == position) \
            .order_by(Portlet.weight.desc())

        def any_group(groups1, groups2):
            for group1 in groups1:
                if group1 in groups2:
                    return True
            return False

        shown_portlets = []
        for p in portlets:
            if any_group(user.groups, p.groups):
                if not any_group(user.groups, p.exclude_groups):
                    shown_portlets.append(p)
        return shown_portlets

    @classmethod
    def get_all(cls, order_by='position', filter_by=None, limit=None):
        """Return all Portlets.

        filter_by: dict -> {'name': 'foo'}

        By default, order by Portlet.position.
        """
        q = cls.query
        q = q.order_by(getattr(Portlet, order_by))
        if filter_by:
            q = q.filter_by(**filter_by)
        if limit:
            q = q.limit(limit)
        return q.all()
