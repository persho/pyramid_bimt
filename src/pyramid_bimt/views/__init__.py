# -*- coding: utf-8 -*-
"""Commonly shared view code."""

from pyramid.security import has_permission
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView as BaseFormView


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
         * removes from schema any nodes that have the ``edit_permission`` set,
           if the current user does not have the permission set in
           ``edit_permission``.

        :returns: result from ``pyramid_deform.FormView.__call__()``
        """
        app_assets.need()
        form_assets.need()

        self.schema.bind(request=self.request)
        for child in self.schema.children:
            if hasattr(child, 'edit_permission'):
                if not has_permission(
                    child.edit_permission,
                    self.request.context,
                    self.request,
                ).boolval:
                    self.schema.__delitem__(child.name)

        result = super(FormView, self).__call__()
        if isinstance(result, dict):  # pragma: no branch
            result['title'] = self.title
        return result
