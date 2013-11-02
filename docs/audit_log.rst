=========
Audit log
=========

The ``pyramid_bimt`` package provides an audit log functionality. This means
that all relevant system events are saved to the DB for future use by admins.
Admins are provided a view where all audit log entries are listed and can be
ordered and searched through.

A single Audit log entry contains the following:
* timestamp
* user id
* audit log event type id
* comment

Audit log event types, provided by default by this package are:
* UserSignedUp
* UserLoggedIn
* UserLoggedOut
* UserChangedPassword
* UserEnabled
* UserDisabled

Event types are stored in the ``audit_log_event_type`` table, so every app
can add its specific event types. A single Audit log event type needs to have
the following information:
* name (usually the same as the class name of the triggered zope.event)
* title (unicode, for UI display)
* description (unicode, for UI display)

Custom per-app event types should start with an ID greater than 1000, to
reserve address space for more pyramid_bimt default event types.

Admins can inspect the log either by direct DB queries or by going to the
``/audit-log`` view, which lists the most recent 100 audit log entries.
