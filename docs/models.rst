Models
======


Base Model Class
----------------

All our models inherit from declarative SQLAlchemy ``Base`` class and the
``BaseMixin`` class provided by ``pyramid_basemodel``.

.. autoclass:: pyramid_basemodel.Base
    :members:

.. autoclass:: pyramid_basemodel.BaseMixin
    :members:

The ``version``, ``created`` and ``modified`` columns are stored as ``v``,
``c`` and ``m``, respectively.

Example:

.. code-block:: python

      >>> class MyModel(Base, BaseMixin):
      ...     __tablename__ = 'my_model'
      ...
      >>> instance = MyModel()
      >>> Session.add(instance)
      >>> # etc.
