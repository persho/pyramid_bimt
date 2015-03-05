Workflows
=========

BIMT provides an integration layer for the ``repoze.workflow`` package to
enable workflow support for BIMT apps' models. Before continuing, read the
`repoze.workflow documentation <http://docs.repoze.org/workflow/>`_ on how
workflows are constructed and used. The BIMT integration layer provides
shortcuts to a subset of ``repoze.workflow`` features to make our code more readable.


Conventions
-----------

We support having multiple workflows for a single model. However, by default
the BIMT code assumes that workflow state is stored in the ``status``
attribute.


Usage
-----

Models that need workflow support should inherit from the ``WorkflowMixin``
class:

.. autoclass:: pyramid_bimt.models.WorkflowMixin
    :members:
