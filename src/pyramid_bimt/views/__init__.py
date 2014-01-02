# -*- coding: utf-8 -*-
"""Commonly shared view code."""

from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView as BaseFormView
from colanderalchemy import SQLAlchemySchemaNode


class FormView(BaseFormView):
    """A base class for forms in BIMT apps.

    Based on ``pyramid_deform.FormView`` with a custom __call__() method.
    """

    def __call__(self):
        """BIMT-specific override of ``pyramid_deform.FormView.__call__()``.

        Along with calling super().__call__() to get all the benefits of
        underlying ``pyramid_deform.FormView`` class, this method also does
        the following:
         * requires static resources needed to render a form in a BIMT app;
         * sets ``self.title`` so the ``form.pt`` template can use it;
         * if ``sqla_schema_class`` is set, it generates a Colander schema
           from SQLAlchemy schema, using ColanderAlchemy.

        :returns: result from ``pyramid_deform.FormView.__call__()``
        """
        app_assets.need()
        form_assets.need()
        if hasattr(self, 'sqla_schema_class') and self.sqla_schema_class:
            fields = self.sqla_schema_class.allowed_fields(
                self.request, mode='edit')
            if not fields:
                raise KeyError('No allowed fields found.')
            self.schema = SQLAlchemySchemaNode(
                self.sqla_schema_class, includes=fields)

        result = super(FormView, self).__call__()
        if isinstance(result, dict):  # pragma: no branch
            result['title'] = self.title
        return result
