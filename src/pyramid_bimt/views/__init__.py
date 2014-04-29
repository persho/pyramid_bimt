# -*- coding: utf-8 -*-
"""Commonly shared view code."""

from collections import OrderedDict
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
            result['description'] = getattr(self, 'description', None)
        return result


class DatatablesDataView(object):
    """Base class for a view that provides AJAX data for jQuery.dataTables.

    Register it to the same route as the view that renders the HTML where
    datatables is included, but use the ``xhr=True`` view predicate. Then,
    use the ``xhr=False`` view predicate for the HTML view.

    .. code-block:: python

        @view_config(
            route_name='foo',
            renderer='json',
            xhr=True,
        )
        class MyDatatablesDataView(DatatablesDataView):
            ...
    """
    #: A list of columns in a table needs to be specified, so we can know by
    #: which column we need to sort after (datatables only gives us a column
    #: number).
    #: If a column supports ordering, then it needs to have the same name
    #: as an SQLAlchemy field by which to order.
    columns = OrderedDict()

    #: Model class that will be used for querying for data. Provide your model
    #: in your derived class.
    model = None

    def __init__(self, request):
        self.request = request

    def populate_columns(self, item):
        """Fill self.columns with display values for given item/row.

        Provide your own populate_columns() method in your derived class.
        """
        raise NotImplemented  # pragma: no cover

    def __call__(self):
        """Returns data that can be fed via AJAX into jQuery.dataTables."""
        # get query parameters
        start = int(self.request.GET.get('iDisplayStart', '0'))
        end = start + int(self.request.GET.get('iDisplayLength', '10'))
        search = self.request.GET.get('sSearch', None)
        order_by = self.columns.keys()[
            int(self.request.GET.get('iSortCol_0', '0'))]
        order_direction = self.request.GET.get('sSortDir_0', 'asc')

        data = []
        for item in self.model.get_all(
            search=search,
            order_by=order_by,
            order_direction=order_direction,
            offset=(start, end)
        ).all():
            for key in self.columns.keys():  # reset columns
                self.columns[key] = None

            self.populate_columns(item)
            data.append(self.columns.values())

        return {
            # An unaltered copy of sEcho sent from the client side.
            'sEcho': int(self.request.GET.get('sEcho', '0')),
            # Total records before any filtering/searching
            'iTotalRecords': self.model.get_all().count(),
            # Total records after filtering/records before pagination
            'iTotalDisplayRecords': self.model.get_all(search=search).count(),
            # List of result contents for current set
            'aaData': data,
        }
