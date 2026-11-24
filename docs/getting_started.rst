Getting Started
===============

Installation
------------

vizit requires Python 3.12 or newer. Install it from a checkout of the
repository:

.. code-block:: console

   $ pip install .

or, for development, an editable install with the test extras:

.. code-block:: console

   $ pip install -e '.[test]'

This installs the ``vizit`` command and the importable :mod:`vizit` package.

Your first plot
---------------

Given a data file ``signal.dat``::

    # time   signal
    0.0      0.10
    1.0      0.22
    2.0      0.31
    3.0      0.28

plot the second column against the first:

.. code-block:: console

   $ vizit line signal.dat -x 1 -c 2

By default vizit opens an interactive window. To save to a file instead (and
skip the window), pass ``-o`` and ``--no-show``:

.. code-block:: console

   $ vizit line signal.dat -x 1 -c 2 -o signal.png --no-show

The data-file model
-------------------

vizit reads whitespace- or delimiter-separated numeric tables:

* **Comments.** Lines whose first non-blank character is ``#`` or ``@`` are
  ignored (configurable with ``--comments``). Blank lines are skipped.
* **Separators.** Comma, tab, semicolon and whitespace are auto-detected;
  explicit delimiters take precedence over whitespace, so a tab-separated file
  with spaces inside a text field is still split correctly. Force one with
  ``-s/--sep`` (e.g. ``-s ,`` for CSV).
* **Headers.** If the first non-comment line looks like a row of names sitting
  above numbers, it is taken as column names, which can then be used in place of
  indices (``-c energy``). Force the behaviour with ``--header`` /
  ``--no-header``.

.. note::

   Column names are read from a plain (non-comment) header line. A
   ``#``-prefixed line is treated as a comment and skipped, so it is **not**
   used for names.

Text columns
------------

Only the columns you actually plot need to be numeric. Scientific data files
routinely carry a label column alongside the numbers::

    # stage   step   T_K       E_pot_kJ_per_mol
    equil     10     597.297   343.947070
    equil     20     594.294   332.271920
    prod      30     300.000   -322.115226

Column 1 here is text. vizit reads the file happily and simply skips it:

.. code-block:: console

   $ vizit line DEMO_ENERGY.dat -c 4          # plot the energy
   $ vizit line DEMO_ENERGY.dat -x 2 -c 3,4   # step vs temperature and energy
   $ vizit line DEMO_ENERGY.dat               # no -c: plots numeric columns 2, 3, 4

When columns are not named explicitly, vizit plots the numeric columns and
ignores text ones. Asking for a text column *is* an error, reported precisely:

.. code-block:: console

   $ vizit line DEMO_ENERGY.dat -c 1
   vizit: DEMO_ENERGY.dat: column 1 is not numeric — line 3 contains 'equil'; numeric columns are 2, 3, 4

From Python, :attr:`~vizit.Dataset.numeric_columns` lists the plottable columns
and :attr:`~vizit.Dataset.non_numeric` maps each text column to the first value
that failed to parse.

Column indexing
---------------

All column references on the command line and in the Python API are
**1-based**: column ``1`` is the first column, matching the convention used by
gnuplot and ``awk``. When no ``x`` column is given, the row number (starting at
0) is used as the x-axis.

Using the Python API
--------------------

The command line is a thin wrapper over the library, so anything you can do
from the shell you can do from Python:

.. code-block:: python

   from vizit import load, line

   ds = load("signal.dat")          # -> a Dataset
   fig = line(ds, cols=[2], x=1, logy=True)
   fig.savefig("signal.png", dpi=300)

Every plotting function returns a :class:`matplotlib.figure.Figure`, so you can
further customise it before saving or showing. See :doc:`api` for the full
reference and :doc:`examples` for a gallery of recipes.
