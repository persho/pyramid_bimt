# -*- coding: utf-8 -*-
"""Custom deform widgets."""

from deform.widget import SelectWidget

import json


class ChosenSelectWidget(SelectWidget):
    """A selection widget using the Chosen jQuery plugin.

    The view rendering a schema with this widget needs to load additional
    static assets:
    from pyramid_bimt.static import chosen_assets
    chosen_assets.need()
    """
    template = 'widget/chosen_select'
    settings = {
        'search_contains': True,
    }

    def serialize(self, field, cstruct, **kw):
        """Add support for passing settings to the Chosen plugin."""
        kw['settings'] = json.dumps(self.settings)
        return super(ChosenSelectWidget, self).serialize(field, cstruct, **kw)
