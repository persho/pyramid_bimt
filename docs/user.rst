==============
Users & Groups
==============

Apps building on top of ``pyramid_bimt`` do not need to handle users & groups,
as that is already provided by the ``pyramid_bimt`` package.

.. autoclass:: pyramid_bimt.models.Group
    :members:

.. autoclass:: pyramid_bimt.models.User
    :members:

Enable/Disable User
===================

We follow a concept of enabled/disabled users:

* enabled members can login and use the app normally
* disabled members can login too, but cannot use the app's normal views, they
  are only allowed to see their account page (``/settings``).

To achieve this, all app views (the ones driving app's business logic) should
be protected by the ``user`` permission. The ``user`` permission is granted to
all users in the ``users`` group. All enabled users are members of the
``users`` group, giving them the ``user`` permission, granting them access
to app views.

The :class:`User <pyramid_bimt.models.User>` model provides a shorthand
for checking if a user is enabled of not: :attr:`user.enabled
<pyramid_bimt.models.User.enabled>`. Enabling/disabling a user is easy, just
call :meth:`user.enable <pyramid_bimt.models.User.enable>` or
:meth:`user.disable <pyramid_bimt.models.User.disable>` and emit the
:class:`UserEnabed <pyramid_bimt.events.UserEnabled>`/:class:`UserDisabled
<pyramid_bimt.events.UserDisabled>` event, respectively.


App-specific User data -- user properties
=========================================

Some apps need to store data for each user, for example: which sources does
the user want to use in BigMediaScraper. However, adding additional columns
to the :class:`User <pyramid_bimt.models.User>` model inside an app's codebase
is not trivial.

To overcome this, ``pyramid_bimt`` provides :class:`user properties
<pyramid_bimt.models.User.properties>`: a field on the ``User`` model where
apps can store arbitrary `key-value` entries. A single entry has the following
definition:

.. autoclass:: pyramid_bimt.models.UserProperty
    :members:

To `get` a user property use :meth:`user.get_property('my_property')
<pyramid_bimt.models.User.get_property>` and to `set` a property use
:meth:`user.set_property('my_property', u'My über value')
<pyramid_bimt.models.User.set_property>`.

