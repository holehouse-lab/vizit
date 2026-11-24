Examples
========

A gallery of common recipes, shown both as shell commands and as the
equivalent Python. All commands assume a data file in the current directory;
the packaged ``vizit/data/look_and_say.dat`` (a single column of integers) is a
handy one to experiment with.

Single column, log scale
------------------------

.. code-block:: console

   $ vizit line look_and_say.dat -c 1 --logy --title "Look and say"

.. code-block:: python

   from vizit import load, line
   line(load("look_and_say.dat"), cols=[1], logy=True, title="Look and say")

Multiple series from one file
-----------------------------

Plot columns 2 and 3 against column 1:

.. code-block:: console

   $ vizit line data.dat -x 1 -c 2,3

.. code-block:: python

   line(load("data.dat"), x=1, cols=[2, 3])

Selecting columns by name
-------------------------

If the file has a header line (``time energy entropy``), refer to columns by
name:

.. code-block:: console

   $ vizit line data.dat -x time -c energy,entropy

.. code-block:: python

   line(load("data.dat"), x="time", cols=["energy", "entropy"])

Scatter with a linear fit
-------------------------

.. code-block:: console

   $ vizit scatter data.dat -x 1 -y 2 --fit

.. code-block:: python

   from vizit import scatter
   scatter(load("data.dat"), x=1, y=2, fit=True)

Error bars
----------

Column 3 holds the uncertainty on column 2:

.. code-block:: console

   $ vizit line data.dat -x 1 -c 2 --yerr 3

.. code-block:: python

   line(load("data.dat"), x=1, cols=[2], yerr=3)

Mean, median and rolling average
--------------------------------

.. code-block:: console

   $ vizit line noisy.dat -c 1 --mean --rolling 20

.. code-block:: python

   line(load("noisy.dat"), cols=[1], mean=True, rolling=20)

Histogram
---------

.. code-block:: console

   $ vizit hist samples.dat -c 1 --bins 30 --density

.. code-block:: python

   from vizit import hist
   hist(load("samples.dat"), cols=[1], bins=30, density=True)

Heatmap of a matrix
-------------------

.. code-block:: console

   $ vizit heatmap contacts.csv --cmap viridis --aspect equal

.. code-block:: python

   from vizit import heatmap
   heatmap(load("contacts.csv"), cmap="viridis", aspect="equal")

Heatmap with a fixed color scale
--------------------------------

Fixing the limits makes separate heatmaps directly comparable:

.. code-block:: console

   $ vizit heatmap run1.csv --vmin 0 --vmax 100 -o run1.png --no-show
   $ vizit heatmap run2.csv --vmin 0 --vmax 100 -o run2.png --no-show

.. code-block:: python

   heatmap(load("run1.csv"), vmin=0, vmax=100, output="run1.png", show=False)

Ratio of two matrices
---------------------

A second file turns the heatmap into the element-wise ratio of the two
matrices. A ratio is a diverging quantity, so the colormap defaults to
``seismic``:

.. code-block:: console

   $ vizit heatmap mutant.csv wildtype.csv

.. code-block:: python

   heatmap(load("mutant.csv"), load("wildtype.csv"))

Ratios sit symmetrically about 1 on a log scale, so a log color scale often
reads best:

.. code-block:: console

   $ vizit heatmap mutant.csv wildtype.csv --log-color --vmin 0.1 --vmax 10

.. code-block:: python

   heatmap(load("mutant.csv"), load("wildtype.csv"), log_color=True, vmin=0.1, vmax=10)

Centring the color scale on zero
--------------------------------

For data that spans zero — differences, log-ratios, ΔΔG — pin zero to the
midpoint colour of the colormap (white, in ``seismic``). The limits become
symmetric, so equal excursions either side of zero are equally intense:

.. code-block:: console

   $ vizit heatmap delta.csv --auto-midpoint-zero

.. code-block:: python

   heatmap(load("delta.csv"), auto_midpoint_zero=True)

Reading from a pipe
-------------------

vizit reads standard input when the filename is ``-``:

.. code-block:: console

   $ awk '{print $1, $5}' raw.log | vizit line - --no-show -o out.png

Saving to PDF/SVG for publications
----------------------------------

The output format is taken from the file extension:

.. code-block:: console

   $ vizit line data.dat -c 2 --style ggplot --figsize 8 5 -o figure.pdf --no-show

.. code-block:: python

   from vizit import PlotConfig, line
   cfg = PlotConfig(style="ggplot", figsize=(8, 5), output="figure.pdf", show=False)
   line(load("data.dat"), cols=[2], config=cfg)

Post-processing the figure
--------------------------

Because every plot function returns a :class:`matplotlib.figure.Figure`, you
can keep customising before saving:

.. code-block:: python

   fig = line(load("data.dat"), cols=[2], show=False)
   ax = fig.axes[0]
   ax.axvspan(10, 20, alpha=0.2, color="red")
   fig.savefig("annotated.png", dpi=300)
