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


Display a nice tooltip
----------------------

To display a nice tooltip on an arbitrary DOM element, do the following:

* add ``data-toggle="tooltip"`` attribute to enable tooltips
* add ``data-placement="right"`` to tell the tooltip where to show itself
* add ``title="foobar"`` to tell the tooltip what text to show

Example:

.. code-block:: html

    <span data-toggle="tooltip" data-placement="right" title="foobar">

More info and options at http://getbootstrap.com/javascript/#tooltips.
