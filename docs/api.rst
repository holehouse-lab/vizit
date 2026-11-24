API Reference
=============

The public API is small: load data into a :class:`~vizit.dataset.Dataset`, then
pass it to a plotting function. Appearance and output are controlled by
:class:`~vizit.plotting.PlotConfig` or by keyword overrides on the plot
functions.

Loading data
------------

.. autofunction:: vizit.load

.. autoclass:: vizit.Dataset
   :members:

Plotting
--------

.. autofunction:: vizit.line

.. autofunction:: vizit.scatter

.. autofunction:: vizit.hist

.. autofunction:: vizit.bar

.. autofunction:: vizit.heatmap

.. autoclass:: vizit.PlotConfig
   :members:

Statistics helpers
------------------

.. automodule:: vizit.stats
   :members:

Backend selection
-----------------

.. automodule:: vizit.backend
   :members:

Exceptions
----------

.. automodule:: vizit._errors
   :members:
