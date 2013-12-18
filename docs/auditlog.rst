=========
Audit log
=========

The ``pyramid_bimt`` package provides an audit log functionality. This allows
all relevant system events to be saved to the DB for future use by our staff:

* staff are provided a view where all audit log entries are listed and can be
  ordered and searched through,
* when viewing a user staff can see user's recent audit log entries.

A single Audit log entry contains the following:

.. autoclass:: pyramid_bimt.models.AuditLogEntry
    :members:


Available event types
---------------------

Audit log event types, provided by default by this package are:

.. automodule:: pyramid_bimt.events
    :synopsis: bllblblb
    :members: UserCreated, UserLoggedIn, UserLoggedOut, UserChangedPassword,
              UserEnabled, UserDisabled



Providing app-specific event types
----------------------------------

Event types are stored in the ``audit_log_event_type`` table, so every app
can add its specific event types. A single Audit log event type needs to have
the following information:

.. autoclass:: pyramid_bimt.models.AuditLogEventType
    :members: name, title, description


Getting an ``AuditLogEventType``
--------------------------------

As a convenience, the ``AuditLogEventType`` provides ``by_name()`` method for
fetching ``AuditLogEventType`` instances from DB by their name:

.. automethod:: pyramid_bimt.models.AuditLogEventType.by_name


Apart form that, as all other models, the ``AuditLogEventType`` models provides
``by_id()`` and ``get_all()`` getter methods, that can be used for fetching
``AuditLogEventType`` instances from the database:

.. automethod:: pyramid_bimt.models.AuditLogEventType.by_id

.. automethod:: pyramid_bimt.models.AuditLogEventType.get_all


