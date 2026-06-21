"""
Pure-numpy analysis helpers used by the plotting layer.

These functions contain no matplotlib dependency so they can be tested and
reused independently. They operate on 1-D arrays of data.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from ._errors import PlotError

__all__ = ["LinearFit", "linear_fit", "rolling_mean", "summary", "Summary"]


class LinearFit(NamedTuple):
    """Result of a degree-1 least-squares fit.

    Attributes
    ----------
    slope : float
        Slope of the fitted line.
    intercept : float
        Intercept of the fitted line.
    r_squared : float
        Coefficient of determination (:math:`R^2`) of the fit.
    """

    slope: float
    intercept: float
    r_squared: float

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Evaluate the fitted line at the given x-values.

        Parameters
        ----------
        x : numpy.ndarray
            Points at which to evaluate the line.

        Returns
        -------
        numpy.ndarray
            ``slope * x + intercept``.
        """
        return self.slope * np.asarray(x, dtype=float) + self.intercept


class Summary(NamedTuple):
    """Basic descriptive statistics for a 1-D array.

    Attributes
    ----------
    mean : float
        Arithmetic mean.
    median : float
        Median value.
    std : float
        Population standard deviation (``ddof=0``).
    """

    mean: float
    median: float
    std: float


def linear_fit(x: np.ndarray, y: np.ndarray) -> LinearFit:
    """Least-squares fit of a straight line ``y = slope * x + intercept``.

    Parameters
    ----------
    x, y : numpy.ndarray
        One-dimensional arrays of equal length with at least two points.

    Returns
    -------
    LinearFit
        Named tuple with ``slope``, ``intercept`` and ``r_squared``.

    Raises
    ------
    PlotError
        If fewer than two points are supplied or the lengths differ.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        raise PlotError("linear fit requires x and y of equal length")
    if x.size < 2:
        raise PlotError("linear fit requires at least two points")

    slope, intercept = np.polyfit(x, y, 1)
    residuals = y - (slope * x + intercept)
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return LinearFit(float(slope), float(intercept), r_squared)


def rolling_mean(y: np.ndarray, window: int) -> np.ndarray:
    """Compute a simple (boxcar) rolling average.

    The output has the same length as the input; the first ``window - 1`` values
    are averages over the available leading points (i.e. the window grows in
    from the left edge), so no NaNs are produced.

    Parameters
    ----------
    y : numpy.ndarray
        One-dimensional input array.
    window : int
        Averaging window length, ``>= 1``.

    Returns
    -------
    numpy.ndarray
        Rolling average, same shape as ``y``.

    Raises
    ------
    PlotError
        If ``window`` is less than 1 or larger than ``len(y)``.
    """
    y = np.asarray(y, dtype=float)
    if window < 1:
        raise PlotError("rolling window must be >= 1")
    if window > y.size:
        raise PlotError(f"rolling window ({window}) is larger than the data ({y.size} points)")
    cumsum = np.cumsum(np.insert(y, 0, 0.0))
    out = np.empty_like(y)
    # Full windows for indices >= window - 1.
    out[window - 1 :] = (cumsum[window:] - cumsum[:-window]) / window
    # Partial (left-edge) windows for the first window - 1 points.
    for i in range(window - 1):
        out[i] = y[: i + 1].mean()
    return out


def summary(y: np.ndarray) -> Summary:
    """Return mean, median and standard deviation of a 1-D array.

    Parameters
    ----------
    y : numpy.ndarray
        One-dimensional input array.

    Returns
    -------
    Summary
        Named tuple ``(mean, median, std)``.

    Raises
    ------
    PlotError
        If ``y`` is empty.
    """
    y = np.asarray(y, dtype=float)
    if y.size == 0:
        raise PlotError("cannot summarise an empty array")
    return Summary(float(np.mean(y)), float(np.median(y)), float(np.std(y)))
