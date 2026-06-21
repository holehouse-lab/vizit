"""
vizit
=====

A simple tool for visualizing scientific data — a lightweight, scriptable
gnuplot replacement built on numpy and matplotlib.

vizit can be used three ways:

* from the shell via the ``vizit`` command (see :mod:`vizit.cli`);
* as a Python library, by loading data and calling a plot function;
* by piping data on standard input (``cat data.dat | vizit line -``).

Examples
--------
>>> from vizit import load, line
>>> ds = load("data.dat")                       # doctest: +SKIP
>>> fig = line(ds, cols=[2, 3], logy=True)      # doctest: +SKIP
"""

from __future__ import annotations

from ._errors import ColumnError, DataError, PlotError, VizitError
from .dataset import Dataset
from .loader import load
from .plotting import PlotConfig, bar, hist, line, scatter

# Version is managed by versioningit. At build/install time it writes
# vizit/_version.py; fall back to the installed package metadata otherwise.
try:
    from ._version import __version__
except ImportError:  # pragma: no cover - only hit in a broken/partial install
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("vizit")
    except PackageNotFoundError:
        __version__ = "0+unknown"

__all__ = [
    "ColumnError",
    "DataError",
    "Dataset",
    "PlotConfig",
    "PlotError",
    "VizitError",
    "__version__",
    "bar",
    "hist",
    "line",
    "load",
    "scatter",
]
