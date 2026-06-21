Welcome to vizit's documentation!
=========================================================

**vizit** is a simple tool for visualizing scientific data — a lightweight,
scriptable replacement for quick gnuplot-style plotting, built on
:mod:`numpy` and :mod:`matplotlib`.

It is designed for the common case of "I have a column of numbers in a text
file and I want to see it" while still handling multi-column data, headers,
comments, log axes, error bars, fits and a handful of plot types. vizit works
three ways:

* as a command-line tool — ``vizit line data.dat -c 2``;
* as a Python library — ``from vizit import load, line``;
* in shell pipelines — ``cat data.dat | vizit line -``.

.. code-block:: console

   $ vizit line trajectory.dat -c 2,3 --logy --title "Energy" -o energy.png

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   cli
   examples
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
