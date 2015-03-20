Conventions & Assumptions
=========================

Code style guide
----------------

First and foremost: **use the English language**. Religiously. This includes:

- Code: comments, variables, class names, filenames, etc.
- Examples and placeholders: only use English names, URLs, domain, etc. for
  placeholders in code, documentation and elsewhere.
- Documentation, configuration files, etc.
- Tickets titles, descriptions & comments, GitHub Pull Requests, inline
  comments, etc.
- Basically everything should be in English, bar two exceptions:

  * emails to dev@niteoweb.com
  * IRC communication

With the choice of language behind us, let's move on to code styling
guidelines. We follow the `plone.api style guide
<http://ploneapi.readthedocs.org/en/latest/contribute/conventions.html>`_. The
guidelines defined in this style guide should be used throughout our codebase,
without much exceptions.

That said, we do have some "overrides" to the rules in `plone.api style guide`:

* We don't need to support Python 2.6, so using ``{}`` (insted of ``{0}``) for
  string formatting is preferred.


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

.. Note:: Do not submit a Pull Request before you are happy with the
  implementation. It creates noise on our dashboard screen's
  "Open Pull Requests" widget and there is a risk that your code will get
  merged and deployed prematurely. Until you are ready, keep your
  implementation in a feature branch on GitHub, and use the `Compare` feature
  to discuss code changes.

To submit a `Pull Request` go to
https://github.com/niteoweb/<PROJECT>/tree/<BRANCH_NAME>. There you should see
a ``Pull Request`` button. Click on it, write some text what you did and
anything else you would like to tell the one who will review your branch, and
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

 * close the ticket OR
 * transition it back to state ``In Progress`` and add more requests for
   changes.


Arbirary storage on Amazon S3
-----------------------------

We use S3 extensively for storing arbitrary files that each project needs.
For every type of storage need, we create a separate "bucket" and a respective
user, that has read/write access to this bucket only.

Our main account is under the ``info@niteoweb.com`` identity, which is managed
by Dejan & Nejc. If you need a new bucket to store sth., ping them to create
the bucket and the respective user and give you access.

Things that we keep on S3 (but not a limited to):

* Travis build artifacts (such as robot-framework screenshots)
* Generated HTML files of per-project Sphinx docs for docs.niteoweb.com
* eBooks for docs.niteoweb.com
* Archive of Papertrail logs for each Heroku-based project
* Archive of PostgreSQL dumps for each Heroku-based project
* Builds & releases of whatever cannot be released as a Python egg and uploaded
  to pypi.niteoweb.com


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
  and as traversal parameters (``/user/<id>``).
* name: **unique** "string id" of an object, must be URL-friendly ASCII, used
  as a key to move values from views to templates and back, etc.
* title: always Unicode, used for user-friendly representation in the UI.


Route naming conventions
""""""""""""""""""""""""

To be consistent throughout the codebase always use the following approach
to name your routes::

    * "route name"    :"route_path"            -- "description"
    * <object>_list   :/<object>s              -- list of objects
    * <object>_view   :/<object>/<id>          -- view of object with id of <id>
    * <object>_edit   :/<object>/<id>/edit     -- edit of object with id of <id>
    * <object>_delete :/<object>/<id>/delete   -- delete object with id of <id>
    * <object>_add    :/<object>/add           -- add a new object


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

Some exceptions exist to the above when
:meth:`route_url <pyramid.request.Request.route_url>` should be used instead,
namely:

* emails
* API calls with callbacks
