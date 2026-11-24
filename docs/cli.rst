Command-line Reference
======================

vizit is invoked as ``vizit <plot> <file> [options]``, where ``<plot>`` is one
of ``line``, ``scatter``, ``hist``, ``bar`` or ``heatmap``. Use ``-`` as the
file to read from standard input.

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

``heatmap``
~~~~~~~~~~~

Render a CSV/TSV matrix with :meth:`~matplotlib.axes.Axes.imshow`. Each row of
the file is a row of the image and each numeric column a column, so a leading
text label column is skipped and a header line supplies the column tick labels.

Supplying a **second file** plots the element-wise ratio ``FILE / FILE2``; the
two matrices must have the same shape. Cells with a zero denominator become
``NaN`` and are left blank rather than becoming infinite.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Meaning
   * - ``FILE2``
     - optional second matrix; the heatmap becomes the ratio ``FILE / FILE2``
   * - ``-c, --cols``
     - 1-based columns forming the matrix, comma-separated
   * - ``--vmin``, ``--vmax``
     - fix the color-scale limits (default: scale to the data range)
   * - ``--cmap``
     - matplotlib colormap name. Defaults to matplotlib's own, or to the diverging
       ``seismic`` for a ratio plot or ``--auto-midpoint-zero``
   * - ``--auto-midpoint-zero``
     - centre the color scale on zero, so zero takes the midpoint colour of the
       colormap (white, in ``seismic``)
   * - ``--log-color``
     - logarithmic color scale; needs strictly positive values
   * - ``--cbar-label``
     - colorbar label (defaults to ``ratio`` or ``value``)
   * - ``--no-colorbar``
     - hide the colorbar
   * - ``--aspect``
     - ``auto`` (default, fills the axes) or ``equal`` (square cells)
   * - ``--origin``
     - ``upper`` (default, first row at top) or ``lower``
   * - ``--interpolation``
     - ``imshow`` interpolation (default ``nearest``, i.e. the raw cells)

Examples:

.. code-block:: console

   $ vizit heatmap contacts.csv --cmap viridis --aspect equal
   $ vizit heatmap mutant.csv wildtype.csv                     # ratio, seismic by default
   $ vizit heatmap mutant.csv wildtype.csv --log-color --vmin 0.1 --vmax 10
   $ vizit heatmap delta.csv --auto-midpoint-zero              # white == zero
   $ vizit heatmap run.csv --vmin 0 --vmax 100 -o run.png --no-show

Fixing ``--vmin``/``--vmax`` is what makes several heatmaps directly comparable;
left alone, each is scaled to its own data range.

``--auto-midpoint-zero`` is for data that spans zero (differences, log-ratios).
It makes the limits symmetric — ``±max(|vmin|, |vmax|)``, or ``±max|value|`` when
no limits are given — so that zero lands exactly on the midpoint colour and equal
excursions either side of zero are equally intense. A matrix spanning ``-8 … 2``
is therefore scaled ``-8 … 8``. It cannot be combined with ``--log-color``, since
a logarithmic scale cannot include zero.

.. note::

   Unlike the other subcommands, ``heatmap`` draws no grid by default (a grid
   over an image is just noise). Pass ``--grid`` if you want one.

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

Text columns
------------

A column only has to be numeric if you plot it. A file with a label column::

    equil   10   597.297   343.947070
    prod    20   300.000   -322.115226

loads fine; ``-c 4`` plots the energy, and omitting ``-c`` altogether plots
every *numeric* column (2, 3, 4), skipping the text one. Selecting a text column
explicitly reports the offending value:

.. code-block:: console

   $ vizit line DEMO_ENERGY.dat -c 1
   vizit: DEMO_ENERGY.dat: column 1 is not numeric — line 3 contains 'equil'; numeric columns are 2, 3, 4

Exit status
-----------

vizit returns ``0`` on success and ``2`` for expected errors (missing file,
bad column, non-numeric column, malformed value), printing a concise
``vizit: ...`` message to standard error without a traceback.
