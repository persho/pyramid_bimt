==========
JavaScript
==========


Show 'secret' info on click
---------------------------

If you need to show a password in a template, use the `secret` span approach.
This means to print ``*`` instead of actual password in the span with class
``secret`` but include the password in the ``data-secret`` attribute. Example:

.. code-block:: html

    <span class="secret" data-secret="mypassword">**********</span>

When user clicks on the span, the ``*`` characters will be replaced with the
actual password, so user can see & copy it.

