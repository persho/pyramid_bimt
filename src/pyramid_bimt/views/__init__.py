# -*- coding: utf-8 -*-
"""Commonly shared view code."""

from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView as BaseFormView
from colanderalchemy import SQLAlchemySchemaNode

import colander
import deform


class FormView(BaseFormView):
    """A base class for forms in BIMT apps.

    Based on :class:`pyramid_deform.FormView` with a custom __call__() method.
    """

    def __call__(self):
        """BIMT-specific override of
        :meth:`pyramid_deform.FormView.__call__()`.

        Along with calling ``super().__call__()`` to get all the benefits of
        underlying :class:`pyramid_deform.FormView` class, this method also
        does the following:

        * `requires` static resources needed to render a form in a BIMT app,
        * hides the sidebar if ``self.hide_sidebar`` is True,
        * if ``sqla_schema_class`` is set, it generates a Colander schema
          from SQLAlchemy schema, using ColanderAlchemy,
        * sets ``self.title`` so the ``form.pt`` template can use it.

        :returns: result from :meth:`pyramid_deform.FormView.__call__()`
        """
        app_assets.need()
        form_assets.need()

        if hasattr(self, 'hide_sidebar') and self.hide_sidebar:
            self.request.layout_manager.layout.hide_sidebar = True

        if hasattr(self, 'sqla_schema_class') and self.sqla_schema_class:
            if hasattr(self, 'sqla_fields') and self.sqla_fields:
                fields = self.sqla_fields
            else:
                fields = self.sqla_schema_class.allowed_fields(
                    self.request, mode='edit')
            if not fields:
                raise KeyError('No allowed fields found.')
            self.schema = SQLAlchemySchemaNode(
                self.sqla_schema_class, includes=fields)

        self.after_schema(self.schema)

        result = super(FormView, self).__call__()
        if isinstance(result, dict):  # pragma: no branch
            result['title'] = self.title
        return result

    def after_schema(self, schema):
        """Performs some processing on the ``schema`` prior to creating a Form.

        By default, this method does nothing. Override this method
        in your derived class to modify the ``schema``. Your function
        will be executed immediately after instantiating the schema
        instance in :meth:`__call__` (thus before creating a Form object).
        """
        pass

    def inject_relationship_field(self, schema, model, before):
        """Inject a SA Relationship SchemaNode into schema.

        Relationships are not well supported in ColanderAlchemy, so if we want
        to have them in forms we need to manually inject SchemaNodes for them.

        :param schema: The schema into which to inject a relationship field.
        :type schema: :class:`colander.Schema` instance
        :param model: The model that is referenced in the relationship. Must
            provide the ``get_all()`` method. Instances of the model must
            provide ``id`` and ``name`` attributes.
        :type model: SQLAlchemy model class
        :param before: Name of the field before which to inject our
            relationship field.
        :type before: string
        """
        instances = model.get_all().all()
        choices = [(instance.id, instance.name) for instance in instances]
        schema.add_before(
            before,
            node=colander.SchemaNode(
                colander.Set(),
                name='{}s'.format(model.__name__.lower()),
                missing=[],
                widget=deform.widget.CheckboxChoiceWidget(values=choices),
            ),
        )
