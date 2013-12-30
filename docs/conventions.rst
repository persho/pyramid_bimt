Conventions & Assumptions
=========================

Code style guide
----------------

We follow `plone.api's style guide
<http://ploneapi.readthedocs.org/en/latest/contribute/conventions.html>`_. Read
it & use it.


Additional conventions
----------------------

Mark changes that require DB migrations
"""""""""""""""""""""""""""""""""""""""

When a change in ``pyramid_bimt`` requires database migration in an app,
prefix the ``CHANGELOG.rst`` entry with ``[DB MIGRATION REQUIRED]``.

When releasing a version which requires DB migration, bump the major version
number, to have one more indication that stuff changes and ``pyramid_bimt``
cannot be blindly upgraded in an app.


Settings page
"""""""""""""

Each app needs to provide its own `settings` page, where users can modify their
own settings, such as email, fullname, etc. and any additional app-specific
configuration. This page is normally served on ``/settings``.


ID vs. name vs. title
"""""""""""""""""""""

To be consistent throughout the codebase always use id/name/title in the
following way:

* id: **unique** database row id number, normally only used for DB maintenance
  and as traversal parameters (``/users/<id>``).
* name: **unique** "string id" of an object, must be URL-friendly ASCII, used
  as a key to move values from views to templates and back, etc.
* title: always unicode, used for user-friendly representation in the UI


Route naming conventions
""""""""""""""""""""""""

To be consistent throughout the codebase always use the following approach
to name your routes::

    * "route path"    :"route_path"             -- "description"
    * <object>s       :/<object>s               -- list of objects
    * <object>_view   :/<object>s/<id>          -- view of object with id of <id>
    * <object>_edit   :/<object>s/<id>/edit     -- edit of object with id of <id>
    * <object>_delete :/<object>s/<id>/delete   -- delete object with id of <id>
    * <object>_add    :/<object>s/add           -- add a new object


Model getters conventions
"""""""""""""""""""""""""

To be consistent throughout the codebase always use the following approach
to name your model getters:

* [required] ``by_id``: get object by id
* [required] ``by_name``: get object by name (if object has ``name`` field)
* [required] ``get_all``: get all objects with default ordering, limit and
  optional filtering
* [optional] ``by_<field_name>``: get object by <field_name>

All getters should return None if no objects found, they should not raise
errors.

If there is query that you use in more than one place, make a getter method
for it on the model.


Testing Unicode fields
""""""""""""""""""""""

Whenever you are interacting with Unicode fields in your tests, use umlauts
(``foö``, ``bär``, etc.) to catch any encoding/decoding errors early.


Generating URLs
"""""""""""""""

Pyramid provides two ways to generate URLs for our route based views:

* :meth:`route_url <pyramid.request.Request.route_url>`
* :meth:`route_path <pyramid.request.Request.route_path>`

In general, the :meth:`route_path <pyramid.request.Request.route_path>` method
should always be preferred over
:meth:`route_url <pyramid.request.Request.route_url>`. The main benefit from
this is that the URLs are protocol agnostic and work always in both `http` and
`https` environments. Additionally, using only the paths will save bytes from
the generated HTML documents.

Some exceptions exists to the above when
:meth:`route_url <pyramid.request.Request.route_url>` should be used instead,
namely:

* emails
* API calls with callbacks
