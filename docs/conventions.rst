Conventions & Assumptions
=========================

Code style guide
----------------

We follow `plone.api's style guide
<http://ploneapi.readthedocs.org/en/latest/contribute/conventions.html>`_. Read
it & use it.


Ticket workflow
---------------

Our Plan.io account contains `a list of open BIMT issues
<https://niteoweb.plan.io/projects/big-im-toolbox/issues?query_id=1>`_. Start
from the top and find the first ticket in state ``New`` that does not yet have
an :term:`Assignee`. Click on it, read the description and see if it contains
everything you need to start working on it. If not, assign it to the
:term:`Reporter` and ask for more info in the comments. If the ticket has all
you need to start working on it, do the following:

* assign it to yourself,
* transition it to state ``In Progress`` so other developers know this issue
  is being worked on and we don't stomp on each others' feet.

Based on our :ref:`git workflow <ploneapi:git_workflow>` all work must happen
in separate git branches.

Once you are happy with your implementation, you are ready to submit a
:term:`Pull Request` to get your work merged into master and deployed into
production.

.. code-block:: bash

    $ git checkout master  # go to master branch
    $ git checkout -b <BRANCH_NAME>  # create a feature branch

    # change code here

    $ git add -p && git commit  # commit changes
    $ git push origin <BRANCH_NAME>  # push branch to GitHub

To submit a `Pull Request` go to
https://github.com/niteoweb/<PROJECT>/tree/<BRANCH_NAME>. There you should see
a ``Pull Request`` button. Click on it, write some text what you did and
anything else you would like to tell the one who will merge your branch, and
finally click ``Send pull request``.

Now wait that someone comes by and reviews/merges your branch (don't do it
yourself, even if you have permissions to do so). You can poke people in IRC to
review it. Once the `Pull Request` is merged, your changes are immediately
pushed to production.

At this point, go back to your ticket on Plan.io and update it like so:

 * assign it to the Reporter
 * transition it to state ``Deployed``
 * log time spent working on the ticket

The Reporter can now go to the production server, check if everything works
as it should and either:

 * close the ticket
 * transition it back to state ``New`` and add more requests for changes


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

    * "route name"    :"route_path"             -- "description"
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
