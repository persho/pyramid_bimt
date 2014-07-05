Deployment
==========

All BIMT apps are deployed on :term:`Heroku`, this document describes how.

Continuous deployment
---------------------

Whenever a change is pushed to ``master`` branch on GitHub, :term:`Travis` runs
all tests for that commit and if successful pushes that latest app code to
Heroku. Heroku then deploys it on `http://bimt-<APP>.herokuapp.com
<http://herokuapp.com>`_.

In other words, to deploy some code to production do:

.. code-block:: bash

    $ git checkout master
    $ git merge <your_feature_branch>
    $ git push origin master

Travis will then build this code and (if successful) deploy to Heroku.

However, **merging your own work is discouraged**. Rather open up a Pull
Request on GitHub so someone else can go through your changes and confirm they
are OK.

If you need to manually push code to Heroku (to skip the Travis step) do this:

.. code-block:: bash

    $ heroku login
    $ heroku keys:add
    $ git push heroku master


Staging
-------

If you are preparing a bigger change it is wise to first deploy your code to
staging. Do this by pushing your code to the ``staging`` branch on GitHub:

.. code-block:: bash

    $ git checkout staging
    $ git merge <your_feature_branch>
    $ git push origin staging

Deploying to staging will also clone the production DB and run any available
``alembic`` DB migration steps.

The staging app is available on `http://bimt-<APP>-staging.herokuapp.com
<http://herokuapp.com>`_.

.. note::

    Sometimes when you force-push code to staging many times, the ``pip
    install`` on Heroku fails. To proceed you need to purge the environment
    so the installation starts from scratch. To do that, temporarily change the
    Python version in ``runtime.txt`` and push the change to Heroku.


Troubleshoot Heroku environment
-------------------------------

To build your environment in the same manner as it's built on Heroku do this:

.. code-block:: bash

    # Build and start the Heroku environment locally
    $ source bin/activate
    $ pip install -r requirements.txt
    $ heroku config:pull --overwrite
    $ foreman start

Heroku uses ``requirements.txt`` to install all dependencies, make sure all
:ref:`version pins <pinning_versions>` in ``versions.cfg`` are also
present in ``requirements.txt``.


Deploy to your own account
--------------------------

If you want, you can deploy the entire app to your own Heroku account:

.. code-block:: bash

    $ heroku login
    $ heroku keys:add
    $ heroku create --stack cedar
    $ heroku apps:rename my-own-app
    $ git push heroku master  # upload code
    $ heroku addons:add heroku-postgresql:dev
    $ heroku pg:promote <HEROKU_POSTGRESQL_URL>
    $ heroku run 'python -m <APP>.scripts.populate etc/production.ini'  # populate db
    $ heroku restart  # restart the app so DB changes take effect
    $ heroku logs -t  # see what's going on
    $ heroku open  # open deployed app in your browser

To redeploy, manually push latest changes to Heroku (not GitHub):

.. code-block:: bash

    $ git push heroku master


Heroku Buildpacks
-----------------

If you need to install a third-party library (such as lftp, unzip, etc.) on
Heroku you should use custom Heroku Buildpacks to achieve it. Each library
should have its dedicated buildpack.

First enable support for multiple buildpacks:

.. code-block:: bash

    $ heroku config:add BUILDPACK_URL=git://github.com/ddollar/heroku-buildpack-multi.git

Then add appropriate buildpacks to ``.buildpacks`` and push to Heroku.

.. code-block:: bash

    $ cat .buildpacks
    git://github.com/heroku/heroku-buildpack-python.git
    git://github.com/niteoweb/heroku-buildpack-unzip.git#v1.0


Versioning
""""""""""

Make sure you always use a specific version of a third-party buildpack, never
use buildpacks directly from master branch. In order to do so, fork a
third-party buildpack to the ``niteoweb`` GitHub organization and tag it:

.. code-block:: bash

    $ git tag v1.0


Useful add-ons
--------------


IRC deploy notifications
""""""""""""""""""""""""

On every deploy we get an IRC notification on ``irc.freenode.org#niteoweb``.
It's configured with:

.. code-block:: bash

    $ heroku addons:add deployhooks:irc
        --server=irc.freenode.org
        --room=niteoweb
        --message="{{user}} deployed {{app}} to {{url}}"

While we're at it, let's also configure IRC notifications from GitHub:

.. code-block:: bash

    $ gem install github_cli
    $ gcli authorize
    $ gcli hook create niteoweb <APP>
        --events=pull_request
        --name=irc
        --config=server:irc.freenode.net port:7000 room:"#niteoweb" ssl:1 message_without_join:1


Log aggregation in Papertrail
"""""""""""""""""""""""""""""

We aggregate all logs in Papertrail:

.. code-block:: bash

    $ heroku addons:add papertrail

Once you have Papertrail ready, you need to prepare Amazon S3 to keep your
log archives for future reference. Amazon S3 is managed via
https://console.aws.amazon.com/.

First, you need to create a `Bucket` to store your backups on S3. Select ``S3``
under ``Services`` in `Amazon AWS Console` and click ``Create Bucket``. Name
it ``bimt-<APP>-logs``.

Then click ``Properties`` -> ``Permissions`` -> ``Add more permissions``:
- Grantee: aws@papertrailapp.com
- check Upload/Delete

Now that the S3 Bucket is ready, login to Papertrail (Heroku Dashboard -> app
resources -> click Papertrail) and set the following:
- Me -> Profile -> Name: NiteoWeb Ltd.
- Me -> Profile -> Timezone: Ljubljana
- Account -> Archive Copy -> Bucket name: bimt-<APP>-logs

Error aggregation in GetSentry
""""""""""""""""""""""""""""""

We track all errors on GetSentry. JS errors are sent to GetSentry via the
`pyramid_raven` add-on (this one depends on the ``SENTRY_DSN`` env variable).
Exceptions (normal, and those swallowed with logger.exception()) are sent to
GetSentry via a Raven logger handler (this one depends on the
``%(sentry_dsn)s`` arg in ``production.ini``.):

.. code-block:: bash

    $ heroku addons:add sentry

Now, log into Sentry (via Heroku Single-Sign-On) and go to Settings -> Manage
Integrations. Enable IRC and configure it like so:
- Server: irc.freenode.net
- Port: 7000
- Room: #niteoweb
- Without join: checked
- Nick: GetSentry
- SSL: checked

Also set the following:
- Account -> Name: <APP TITLE>
- Appearance -> Timezone: Ljubljana


Network & DB metrics aggregation in Librato Metrics
"""""""""""""""""""""""""""""""""""""""""""""""""""

We graph Heroku router, dyno and postgres metrics using Librato Metrics. Enable
with:

.. code-block:: bash

    $ heroku labs:enable log-runtime-metrics
    $ heroku addons:add librato


Application Performance metrics aggregation in New Relic
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

We use New Relic for application performance monitoring & management. Enable
with:

.. code-block:: bash

    $ heroku addons:add newrelic:stark


Sending emails via Mailgun
""""""""""""""""""""""""""

We use MailGun to send out emails:

.. code-block:: bash

    $ heroku addons:add mailgun

Now go to MailGun control-panel and add & configure a domain for your app.
Enable tracking of HTML emails & clicks.

After your domain is ready, configure your app to use the correct postmaster
account:

.. code-block:: bash

    $ heroku config:set MAILGUN_SMTP_LOGIN=postmaster@<APP_DOMAIN>.com
    $ heroku config:set MAILGUN_SMTP_PASSWORD=<PASSWORD>



Scheduled maintenance scripts with Heroku Scheduler
"""""""""""""""""""""""""""""""""""""""""""""""""""

We run daily maintenance scripts with Heroku Scheduler:

.. code-block:: bash

    $ heroku addons:add scheduler
    $ heroku addons:open scheduler

Add the following BIMT scripts (plus any additional app-specific ones):

.. code-block:: bash

    python -m pyramid_bimt.scripts.expire_subscriptions etc/production.ini
    python -m pyramid_bimt.scripts.sanity_check_email etc/production.ini


On-site PostgreSQL backups
""""""""""""""""""""""""""

This enables daily postgres backups:

.. code-block:: bash

    $ heroku addons:add pgbackups:auto-month


Off-site PostgreSQL backups
"""""""""""""""""""""""""""

Besides onsite backups, we also need off-site backups in case something
happens to Heroku. Configure them by using the `pgbackups-archive-app
<https://github.com/kbaum/pgbackups-archive-app>`_:

.. code-block:: bash

    # create app
    $ cd /tmp
    $ git clone https://github.com/kbaum/pgbackups-archive-app.git
    $ cd pgbackups-archive-app
    $ heroku login
    $ heroku create --stack cedar
    $ heroku apps:rename bimt-<APP>-backups

    # required add-ons
    $ heroku addons:add scheduler:standard
    $ heroku addons:add pgbackups

    # configure scheduler
    $ heroku addons:open scheduler
    # add a new job:
      * task: rake pgbackups:archive
      * dyno size: 1x
      * frequency: daily
      * next run: 6am

    # set environment variables
    $ heroku config:add PGBACKUPS_AWS_ACCESS_KEY_ID="AKIAJLKTIPADANP5S6JQ"
    $ heroku config:add PGBACKUPS_AWS_SECRET_ACCESS_KEY="<in 1Password>"
    $ heroku config:add PGBACKUPS_BUCKET="bimt-<APP>-backups"
    $ heroku config:add PGBACKUPS_REGION="us-east-1"
    $ heroku config:add PGBACKUPS_DATABASE_URL="<main app's DATABASE_URL>"

    # start the backups app
    $ git push heroku master
    $ heroku restart

Once the Heroku app is up & running, you need to prepare Amazon S3 to keep your
backups. Amazon S3 is managed via https://console.aws.amazon.com/.

First, you need to create a `Bucket` to store your backups on S3. Select ``S3``
under ``Services`` in `Amazon AWS Console` and click ``Create Bucket``. Name
it ``bimt-<APP>-backups``.

Then click ``Properties`` -> ``Lifecycle`` -> ``Add rule``:

* Enabled: true
* Name: Archive to Glacier
* Apply to Entire Bucket: true
* Time Period Format: Days from creation date
* Move to Glacier: 30 days from object's creation date

Backups are uploaded as the ``bimt-backups`` user. Make sure the user exists
and and that it has the user policy defined below. Your new bucket needs to
be on the list of resources:

.. code-block:: json

    {
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "s3:ListAllMyBuckets",
          "Resource": "arn:aws:s3:::*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "s3:ListBucket",
            "s3:ListObject",
            "s3:PutObject"
          ],
          "Resource": [
            "arn:aws:s3:::bimt-<APP1>-backups",
            "arn:aws:s3:::bimt-<APP1>-backups/*",
            "arn:aws:s3:::bimt-<APP2>-backups",
            "arn:aws:s3:::bimt-<APP2>-backups/*"
          ]
        }
      ]
    }

