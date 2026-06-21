Command-line Reference
======================

vizit is invoked as ``vizit <plot> <file> [options]``, where ``<plot>`` is one
of ``line``, ``scatter``, ``hist`` or ``bar``. Use ``-`` as the file to read
from standard input.

.. code-block:: console

   $ vizit --version
   $ vizit line --help

All subcommands share the input, axis, style and output options listed below;
each subcommand adds its own column-selection and plot-specific flags.

Subcommands
-----------

``line``
~~~~~~~~

Line plot of one or more y columns against an x column (or the row index),
with optional statistical overlays.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Meaning
   * - ``-c, --cols``
     - 1-based y columns, comma-separated (e.g. ``2,3,4``)
   * - ``-x``
     - 1-based x column (default: row index)
   * - ``--yerr``
     - column of symmetric y error magnitudes
   * - ``--mean``
     - overlay the mean of each series
   * - ``--median``
     - overlay the median of each series
   * - ``--fit``
     - overlay a linear least-squares fit of each series
   * - ``--rolling N``
     - overlay a rolling average with window ``N``

``scatter``
~~~~~~~~~~~

Scatter plot of one column against another.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Meaning
   * - ``-x``
     - 1-based x column (default: row index)
   * - ``-y``
     - 1-based y column
   * - ``--yerr``
     - column of symmetric y error magnitudes
   * - ``--fit``
     - overlay a linear least-squares fit

``hist``
~~~~~~~~

Histogram of one or more columns.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Meaning
   * - ``-c, --cols``
     - 1-based columns, comma-separated
   * - ``--bins N``
     - number of bins (default: 10)
   * - ``--density``
     - normalise to a probability density

``bar``
~~~~~~~

Bar chart of one or more value columns. Multiple columns produce grouped bars.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Meaning
   * - ``-c, --cols``
     - 1-based value columns, comma-separated
   * - ``-x``
     - 1-based column for bar positions (default: row index)

Shared options
--------------

Input
~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Flag
     - Meaning
   * - ``-s, --sep SEP``
     - column separator (default: auto-detect)
   * - ``--comments CHARS``
     - comment-line markers (default: ``#@``)
   * - ``--header`` / ``--no-header``
     - force / disable the column-name header line
   * - ``--skip-rows N``
     - discard ``N`` leading data rows

Axes
~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Flag
     - Meaning
   * - ``--xlabel`` / ``--ylabel``
     - axis labels
   * - ``--title``
     - figure title
   * - ``--xlim LO,HI``
     - x-axis limits (either side may be blank)
   * - ``--ylim LO,HI``
     - y-axis limits
   * - ``--logx`` / ``--logy``
     - logarithmic axis
   * - ``--symlogx`` / ``--symlogy``
     - symmetric-log axis (handles zero/negatives)
   * - ``--grid`` / ``--no-grid``
     - toggle the background grid (default: on)
   * - ``--no-legend``
     - hide the legend

Style
~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Flag
     - Meaning
   * - ``--style NAME``
     - matplotlib style (e.g. ``ggplot``)
   * - ``--color C``
     - series color (repeatable)
   * - ``--marker M``
     - series marker (repeatable)
   * - ``--figsize W H``
     - figure size in inches
   * - ``--dpi N``
     - output resolution (default: 150)

Output
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Flag
     - Meaning
   * - ``-o, --output PATH``
     - save figure; format from extension (png/pdf/svg)
   * - ``--no-show``
     - do not open an interactive window

.. note::

   When no display is available (for example over SSH without X forwarding),
   vizit automatically renders headlessly. Use ``-o`` to capture the figure.

Exit status
-----------

vizit returns ``0`` on success and ``2`` for expected errors (missing file,
bad column, malformed value), printing a concise ``vizit: ...`` message to
standard error without a traceback.
