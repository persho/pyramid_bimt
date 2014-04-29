# -*- coding: utf-8 -*-
"""Portlet models."""


from flufl.enum import Enum
from pyramid_basemodel import Base
from pyramid_basemodel import BaseMixin
from pyramid.renderers import render
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

    def get_rendered_portlet(self):
        """Get rendered portlet html"""
        return render(
            'pyramid_bimt:templates/portlet.pt',
            {'content': self.html}
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
