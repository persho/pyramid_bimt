# -*- coding: utf-8 -*-
"""Commonly shared view code."""

from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView as BaseFormView


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
        * sets ``self.title`` so the ``form.pt`` template can use it.

        :returns: result from :meth:`pyramid_deform.FormView.__call__()`
        """
        app_assets.need()
        form_assets.need()

        if hasattr(self, 'hide_sidebar') and self.hide_sidebar:
            self.request.layout_manager.layout.hide_sidebar = True

        result = super(FormView, self).__call__()
        if isinstance(result, dict):  # pragma: no branch
            result['title'] = self.title
        return result
