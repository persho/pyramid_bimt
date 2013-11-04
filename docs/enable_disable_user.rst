===================
Enable/Disable User
===================

We follow a concept of enabled/disabled members:

* enabled members can login and use the app normally
* disabled members can login too, but cannot use the app's normal views, they
  are only allowed to see their account page

To achieve this, all app views (the ones driving the app' business logic)
should be protected by the 'user' permission. The 'user' permission is granted
to all users in the 'users' group. All enabled users are members of the 'users'
group, giving them the 'user' permission, granting them access to app views.

The User model provides a shorthand for checking if a user is enabled of not:
``user.enable``. Enabling/disabling a user is easy, just call ``user.enable()``
or ``user.disable()`` and emit the ``UserEnabled``/``UserDisabled`` event,
respectively.