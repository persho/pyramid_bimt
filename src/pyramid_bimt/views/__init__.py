# -*- coding: utf-8 -*-
"""Commonly shared view code."""

from collections import OrderedDict
from deform.form import Button
from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid_bimt.events import IUserCreated
from pyramid_bimt.models import User
from pyramid_bimt.security import generate
from pyramid_bimt.static import app_assets
from pyramid_bimt.static import form_assets
from pyramid_deform import FormView as BaseFormView

import colander
import deform
import re


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
            self.request.layout_manager.layout.title = self.title
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
        filter_by_name = self.request.GET.get('filter_by.name', None)
        filter_by_value = self.request.GET.get('filter_by.value', None)
        start = int(self.request.GET.get('iDisplayStart', '0'))
        end = start + int(self.request.GET.get('iDisplayLength', '10'))
        search = self.request.GET.get('sSearch', None)
        order_by = self.columns.keys()[
            int(self.request.GET.get('iSortCol_0', '0'))]
        order_direction = self.request.GET.get('sSortDir_0', 'asc')

        security = False if self.request.user.admin else True
        if filter_by_name and filter_by_value:
            filter_by = {filter_by_name: filter_by_value}
        else:
            filter_by = None

        data = []
        for item in self.model.get_all(
                filter_by=filter_by,
                search=search,
                order_by=order_by,
                order_direction=order_direction,
                offset=(start, end),
                security=security,
        ).all():
            for key in self.columns.keys():  # reset columns
                self.columns[key] = None

            self.populate_columns(item)

            row = {}

            # support for assigning classes to TRs
            if self.columns.get('DT_RowClass'):  # pragma: no branch
                row['DT_RowClass'] = self.columns['DT_RowClass']
                del self.columns['DT_RowClass']

            for index, value in enumerate(self.columns.values()):
                row[index] = value

            data.append(row)

        return {
            # An unaltered copy of sEcho sent from the client side.
            'sEcho': int(self.request.GET.get('sEcho', '0')),
            # Total records before any filtering/searching
            'iTotalRecords': self.model.get_all(security=security).count(),
            # Total records after filtering/records before pagination
            'iTotalDisplayRecords': self.model.get_all(
                filter_by=filter_by,
                search=search,
                security=security
            ).count(),
            # List of result contents for current set
            'aaData': data,
        }


# Apps can use this validator for their settings views
@colander.deferred
def deferred_settings_email_validator(node, kw):
    """Validator for setting email in settings, checks for email duplicates"""
    request = kw['request']

    def validator(node, cstruct):
        colander.Email()(node, cstruct)
        if request.user.email != cstruct and User.by_email(cstruct):
            raise colander.Invalid(
                node,
                u'Email {} is already in use by another user.'.format(cstruct)
            )
    return validator


class SettingsSchema(colander.MappingSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=deferred_settings_email_validator,
    )

    api_key = colander.SchemaNode(
        colander.String(),
        missing='',
        title='API key',
        widget=deform.widget.TextInputWidget(
            template='readonly/textinput'
        )
    )


class SettingsForm(FormView):
    schema = SettingsSchema()
    title = 'Settings'
    form_options = (('formid', 'settings'), ('method', 'POST'))

    def __call__(self):
        self.buttons = (
            'save',
            Button(name='regenerate_api_key', title='Regenerate API key'),
        )
        if self.request.user.unsubscribed:
            subscribe_button = Button(
                name='subscribe_to_newsletter',
                title='Subscribe to newsletter'
            )
            self.buttons = self.buttons + (subscribe_button, )
        return super(SettingsForm, self).__call__()

    def save_success(self, appstruct):
        user = self.request.user
        headers = None

        # if email was modified, we need to re-set the user's session
        email = appstruct['email'].lower()
        if user.email != email:
            user.email = email
            headers = remember(self.request, user.email)
        self.request.session.flash(u'Your changes have been saved.')
        return HTTPFound(location=self.request.path_url, headers=headers)

    def regenerate_api_key_success(self, appstruct):
        self.request.user.set_property('api_key', generate_api_key())
        self.request.session.flash(u'API key re-generated.')

    def subscribe_to_newsletter_success(self, appstruct):
        self.request.session.flash(
            u'You have been subscribed to newsletter.')
        self.request.user.subscribe()
        return HTTPFound(location=self.request.path_url)

    def appstruct(self):
        user = self.request.user
        return {
            'email': user.email,
            'api_key': user.get_property('api_key', ''),
        }


def generate_api_key():
    return re.sub(
        r'(....)(....)(....)(....)', r'\1-\2-\3-\4', unicode(generate(size=16))
    )


@subscriber(IUserCreated)
def set_api_key(event):
    event.user.set_property('api_key', generate_api_key())
